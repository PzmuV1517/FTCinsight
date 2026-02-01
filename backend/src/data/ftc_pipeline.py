"""
FTC Insight Data Pipeline

Complete data ingestion, processing, and storage pipeline for FTC data.
This replaces the TBA-based pipeline with FTC Events API + Local SQL database.
"""

import time
from collections import defaultdict
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple

from src.ftc_api.read_ftc import (
    get_teams,
    get_events,
    get_event_teams,
    get_event_matches,
    get_event_rankings,
    get_event_scores,
)
from src.types.enums import CompLevel, EventStatus, FTCEventType, MatchStatus, MatchWinner
from src.db.sql_storage import (
    write_teams,
    write_team_years,
    write_events,
    write_matches,
    write_team_events,
    write_team_matches,
    write_year,
    write_rankings,
    write_metadata,
    read_metadata,
    read_team_years,
    init_db,
    reset_db,
)


class Timer:
    """Simple timer for performance logging"""
    def __init__(self):
        self.start = time.time()
        self.last = self.start
    
    def log(self, message: str):
        now = time.time()
        elapsed = now - self.last
        total = now - self.start
        print(f"[{total:.1f}s] {message} ({elapsed:.2f}s)")
        self.last = now


def calculate_epa(
    matches: List[Dict],
    team_num: int,
    prior_epa: float = 20.0,
    k_factor: float = 0.2,
) -> Dict[str, float]:
    """
    Calculate EPA (Expected Points Added) for a team
    
    EPA is a measure of how many points a team contributes above/below average.
    Uses an Elo-like update system based on match performance.
    
    Args:
        matches: List of match dictionaries the team participated in
        team_num: Team number to calculate EPA for
        prior_epa: Starting EPA value
        k_factor: Learning rate for EPA updates
    
    Returns:
        Dictionary with EPA components
    """
    if not matches:
        return {
            "epa": prior_epa,
            "auto_epa": prior_epa * 0.3,
            "teleop_epa": prior_epa * 0.5,
            "endgame_epa": prior_epa * 0.2,
            "epa_max": prior_epa,
            "epa_start": prior_epa,
            "count": 0,
        }
    return calculate_epa_impl(matches, team_num, prior_epa, k_factor)


def calculate_win_prob(red_epa: float, blue_epa: float, score_sd: float) -> float:
    """
    Calculate win probability for red alliance based on EPA difference.
    Uses a logistic function similar to Elo rating system.
    
    Args:
        red_epa: Combined EPA of red alliance
        blue_epa: Combined EPA of blue alliance
        score_sd: Standard deviation of scores for the year
    
    Returns:
        Probability that red alliance wins (0.0 to 1.0)
    """
    if score_sd <= 0:
        score_sd = 50  # Default fallback
    
    # Normalize the EPA difference by score_sd
    # Each team contributes ~half their EPA to alliance score
    red_pred = red_epa * 2  # 2 teams on alliance
    blue_pred = blue_epa * 2
    
    diff = red_pred - blue_pred
    norm_diff = diff / score_sd
    
    # Logistic function: k = -5/8 tuned for FRC, adjust for FTC
    k = -0.8  # Slightly more extreme for FTC
    win_prob = 1 / (1 + 10 ** (k * norm_diff))
    
    # Clamp to reasonable range
    return max(0.01, min(0.99, round(win_prob, 4)))


def add_match_predictions(
    matches: List[Dict],
    team_epas: Dict[int, float],
    score_sd: float,
) -> None:
    """
    Add win probability and score predictions to matches in-place.
    
    Args:
        matches: List of match dictionaries to update
        team_epas: Dictionary mapping team numbers to EPA values
        score_sd: Standard deviation of scores for the year
    """
    default_epa = 20.0
    
    for match in matches:
        red_1 = match.get("red_1")
        red_2 = match.get("red_2")
        blue_1 = match.get("blue_1")
        blue_2 = match.get("blue_2")
        
        # Get EPAs, default to average if team not found
        red_1_epa = team_epas.get(red_1, default_epa) if red_1 else default_epa
        red_2_epa = team_epas.get(red_2, default_epa) if red_2 else default_epa
        blue_1_epa = team_epas.get(blue_1, default_epa) if blue_1 else default_epa
        blue_2_epa = team_epas.get(blue_2, default_epa) if blue_2 else default_epa
        
        red_total_epa = red_1_epa + red_2_epa
        blue_total_epa = blue_1_epa + blue_2_epa
        
        # Calculate win probability
        win_prob = calculate_win_prob(red_total_epa / 2, blue_total_epa / 2, score_sd)
        
        # Predict scores (EPA represents points above average, so add to mean)
        # Average match has ~score_mean points per alliance
        score_mean = score_sd * 1.5  # Rough approximation
        red_pred = round(red_total_epa + score_mean, 2)
        blue_pred = round(blue_total_epa + score_mean, 2)
        
        # Set predictions on match
        match["epa_win_prob"] = win_prob
        match["epa_red_score_pred"] = red_pred
        match["epa_blue_score_pred"] = blue_pred
        
        # Predicted winner
        match["epa_winner"] = MatchWinner.RED.value if win_prob >= 0.5 else MatchWinner.BLUE.value


def calculate_epa_with_history(
    matches: List[Dict],
    team_num: int,
    prior_epa: float = 20.0,
    k_factor: float = 0.2,
) -> Tuple[Dict[str, float], Dict[str, Dict[str, float]]]:
    """
    Calculate EPA with progression history for each match.
    
    Returns:
        Tuple of:
        - Final EPA stats dict
        - Dictionary mapping match_key -> {epa, post_epa, auto_epa, teleop_epa, endgame_epa}
    """
    epa = prior_epa
    auto_epa = prior_epa * 0.3
    teleop_epa = prior_epa * 0.5
    endgame_epa = prior_epa * 0.2
    
    epa_max = epa
    epa_start = epa
    count = 0
    
    # Track EPA history per match
    match_epa_history: Dict[str, Dict[str, float]] = {}
    
    # Sort matches by time
    sorted_matches = sorted(matches, key=lambda m: m.get("time", 0))
    
    for match in sorted_matches:
        match_key = match.get("key")
        
        # Store pre-match EPA
        pre_epa = epa
        pre_auto_epa = auto_epa
        pre_teleop_epa = teleop_epa
        pre_endgame_epa = endgame_epa
        
        if match.get("status") != MatchStatus.COMPLETED.value:
            # For non-completed matches, store current EPA as both pre and post
            match_epa_history[match_key] = {
                "epa": round(epa, 2),
                "post_epa": round(epa, 2),
                "auto_epa": round(auto_epa, 2),
                "teleop_epa": round(teleop_epa, 2),
                "endgame_epa": round(endgame_epa, 2),
                "post_auto_epa": round(auto_epa, 2),
                "post_teleop_epa": round(teleop_epa, 2),
                "post_endgame_epa": round(endgame_epa, 2),
            }
            continue
        
        # Determine which alliance the team is on
        red_teams = [match.get("red_1"), match.get("red_2")]
        blue_teams = [match.get("blue_1"), match.get("blue_2")]
        
        if team_num in red_teams:
            alliance = "red"
            score = match.get("red_score", 0) or 0
            opp_score = match.get("blue_score", 0) or 0
            breakdown = match.get("red_score_breakdown", {}) or {}
        elif team_num in blue_teams:
            alliance = "blue"
            score = match.get("blue_score", 0) or 0
            opp_score = match.get("red_score", 0) or 0
            breakdown = match.get("blue_score_breakdown", {}) or {}
        else:
            continue
        
        # Update EPA based on performance (per-robot contribution)
        epa_update = k_factor * (score / 2 - epa)
        epa = max(0, epa + epa_update)
        epa_max = max(epa_max, epa)
        
        # Update component EPAs
        auto_score = breakdown.get("auto_points", 0) or 0
        teleop_score = breakdown.get("teleop_points", 0) or 0
        endgame_score = breakdown.get("endgame_points", 0) or 0
        
        if auto_score + teleop_score + endgame_score > 0:
            auto_epa = max(0, auto_epa + k_factor * (auto_score / 2 - auto_epa))
            teleop_epa = max(0, teleop_epa + k_factor * (teleop_score / 2 - teleop_epa))
            endgame_epa = max(0, endgame_epa + k_factor * (endgame_score / 2 - endgame_epa))
        
        # Store EPA progression for this match
        match_epa_history[match_key] = {
            "epa": round(pre_epa, 2),           # EPA before this match
            "post_epa": round(epa, 2),          # EPA after this match
            "auto_epa": round(pre_auto_epa, 2),
            "teleop_epa": round(pre_teleop_epa, 2),
            "endgame_epa": round(pre_endgame_epa, 2),
            "post_auto_epa": round(auto_epa, 2),
            "post_teleop_epa": round(teleop_epa, 2),
            "post_endgame_epa": round(endgame_epa, 2),
        }
        
        count += 1
    
    final_stats = {
        "epa": round(epa, 2),
        "auto_epa": round(auto_epa, 2),
        "teleop_epa": round(teleop_epa, 2),
        "endgame_epa": round(endgame_epa, 2),
        "epa_max": round(epa_max, 2),
        "epa_start": round(epa_start, 2),
        "count": count,
    }
    
    return final_stats, match_epa_history


def calculate_epa_impl(
    matches: List[Dict],
    team_num: int,
    prior_epa: float = 20.0,
    k_factor: float = 0.2,
) -> Dict[str, float]:
    """
    Calculate EPA implementation - does the actual calculation.
    Returns only final stats (for backward compatibility).
    """
    final_stats, _ = calculate_epa_with_history(matches, team_num, prior_epa, k_factor)
    return final_stats


def calculate_record(matches: List[Dict], team_num: int) -> Dict[str, int | float]:
    """Calculate win/loss/tie record for a team"""
    wins = 0
    losses = 0
    ties = 0
    
    for match in matches:
        if match.get("status") != MatchStatus.COMPLETED.value:
            continue
        
        red_teams = [match.get("red_1"), match.get("red_2")]
        blue_teams = [match.get("blue_1"), match.get("blue_2")]
        winner = match.get("winner")
        
        if team_num in red_teams:
            if winner == MatchWinner.RED.value:
                wins += 1
            elif winner == MatchWinner.BLUE.value:
                losses += 1
            elif winner == MatchWinner.TIE.value:
                ties += 1
        elif team_num in blue_teams:
            if winner == MatchWinner.BLUE.value:
                wins += 1
            elif winner == MatchWinner.RED.value:
                losses += 1
            elif winner == MatchWinner.TIE.value:
                ties += 1
    
    total = wins + losses + ties
    winrate = wins / total if total > 0 else 0

    return {
        "wins": wins,
        "losses": losses,
        "ties": ties,
        "count": total,
        "winrate": round(winrate, 3),
    }


def determine_event_status(matches: List[Dict], event_data: Dict) -> str:
    """Determine the status of an event based on its dates and matches"""
    from datetime import datetime, date
    
    today = date.today()
    
    # Parse event dates
    start_date_str = event_data.get("start_date", "")
    end_date_str = event_data.get("end_date", "")
    
    start_date = None
    end_date = None
    
    try:
        if start_date_str:
            start_date = datetime.strptime(start_date_str, "%Y-%m-%d").date()
        if end_date_str:
            end_date = datetime.strptime(end_date_str, "%Y-%m-%d").date()
    except ValueError:
        pass
    
    # Determine status based on dates (improved logic)
    # If end date is in the past, event is completed regardless of matches
    if end_date and today > end_date:
        return EventStatus.COMPLETED.value
    
    # If start date is in the future, event is upcoming
    if start_date and today < start_date:
        return EventStatus.UPCOMING.value
    
    # If we're between start and end date, check matches to determine status
    if start_date and end_date and start_date <= today <= end_date:
        # During event dates - check if matches are completed
        if matches:
            completed = sum(1 for m in matches if m.get("status") == MatchStatus.COMPLETED.value)
            total = len(matches)
            if completed == total and completed > 0:
                return EventStatus.COMPLETED.value
            elif completed > 0:
                return EventStatus.ONGOING.value
        return EventStatus.ONGOING.value
    
    # If we only have start_date and it's in the past with no end_date
    if start_date and today >= start_date and not end_date:
        # Use match-based logic to determine if completed
        if matches:
            completed = sum(1 for m in matches if m.get("status") == MatchStatus.COMPLETED.value)
            total = len(matches)
            if completed == total and completed > 0:
                return EventStatus.COMPLETED.value
            elif completed > 0:
                return EventStatus.ONGOING.value
        # Event started but we can't determine if it ended
        return EventStatus.COMPLETED.value  # Assume completed if start date passed
    
    # Fallback to match-based logic if no date info
    if matches:
        completed = sum(1 for m in matches if m.get("status") == MatchStatus.COMPLETED.value)
        total = len(matches)
        if completed == 0:
            return EventStatus.UPCOMING.value
        elif completed < total:
            return EventStatus.ONGOING.value
        else:
            return EventStatus.COMPLETED.value
    
    # No dates, no matches - default to upcoming
    return EventStatus.UPCOMING.value


def process_single_event(event: Dict, season: int, cache: bool) -> Dict[str, Any]:
    """
    Process a single event - can be run in parallel.
    
    Returns:
        Dictionary with event data, matches, team_events, rankings
    """
    event_key = event["key"]
    event_code = event.get("event_code", event_key.split("_")[1] if "_" in event_key else event_key)
    
    result = {
        "event": event,
        "matches": [],
        "team_events": [],
        "rankings": [],
        "event_teams": [],
        "error": None,
    }
    
    try:
        # Get teams at this event
        event_teams, _ = get_event_teams(season, event_code, cache=cache)
        result["event_teams"] = event_teams
        
        # Determine event status based on dates
        event_status = determine_event_status([], event)
        
        # Create team-event records with all required fields
        for team_num in event_teams:
            result["team_events"].append({
                "team": team_num,
                "event": event_key,
                "year": season,
                "time": event.get("time", 0),
                "team_name": "",  # Will be populated later from teams data
                "event_name": event.get("name", ""),
                "country": event.get("country"),
                "state": event.get("state"),
                "district": event.get("district"),
                "type": event.get("type", "other"),
                "week": event.get("week", 0),
                "status": event_status,
                "first_event": False,  # Will be calculated later
                "wins": 0,
                "losses": 0,
                "ties": 0,
                "count": 0,
                "winrate": 0,
                "qual_wins": 0,
                "qual_losses": 0,
                "qual_ties": 0,
                "qual_count": 0,
                "qual_winrate": 0,
                "rps": 0,
                "rps_per_match": 0,
            })
        
        # Get matches
        matches, _ = get_event_matches(season, event_code, event.get("time", 0), cache=cache)
        
        # Get detailed score breakdowns
        qual_scores = get_event_scores(season, event_code, "qual", cache=cache)
        playoff_scores = get_event_scores(season, event_code, "playoff", cache=cache)
        
        # Merge score breakdowns into matches
        event_week = event.get("week", 0)
        for match in matches:
            match_num = match.get("match_number", 0)
            comp_level = match.get("comp_level")
            
            # Set week from event
            match["week"] = event_week
            
            if comp_level == CompLevel.QUAL.value and match_num in qual_scores:
                red_bd, blue_bd = qual_scores[match_num]
                match["red_score_breakdown"] = red_bd
                match["blue_score_breakdown"] = blue_bd
            elif match_num in playoff_scores:
                red_bd, blue_bd = playoff_scores[match_num]
                match["red_score_breakdown"] = red_bd
                match["blue_score_breakdown"] = blue_bd
            
            # Convert enums to values for storage
            match["comp_level"] = match["comp_level"].value if hasattr(match["comp_level"], "value") else match["comp_level"]
            match["status"] = match["status"].value if hasattr(match["status"], "value") else match["status"]
            match["winner"] = match["winner"].value if match.get("winner") and hasattr(match["winner"], "value") else match.get("winner")
            
            result["matches"].append(match)
        
        # Get rankings
        rankings, _ = get_event_rankings(season, event_code, cache=cache)
        for team_num, rank in rankings.items():
            result["rankings"].append({
                "event": event_key,
                "team": team_num,
                "rank": rank,
            })
        
        # Update event status
        event["status"] = determine_event_status(matches, event)
        event["num_teams"] = len(event_teams)
        event["match_count"] = len(matches)
        
        # Convert event type enum
        if hasattr(event.get("type"), "value"):
            event["type"] = event["type"].value
            
    except Exception as e:
        result["error"] = f"Event {event_key}: {str(e)}"
    
    return result


def process_season(
    season: int,
    cache: bool = True,
    full_refresh: bool = False,
    max_workers: int = 10,
) -> Dict[str, Any]:
    """
    Process a complete FTC season with parallel event processing
    
    Args:
        season: The season year (e.g., 2024 for 2024-2025 season)
        cache: Whether to use cached API responses
        full_refresh: If True, refresh all data regardless of cache
        max_workers: Number of parallel workers for event processing
    
    Returns:
        Summary statistics of the processing
    """
    from concurrent.futures import ThreadPoolExecutor, as_completed
    
    timer = Timer()
    stats = {
        "season": season,
        "teams": 0,
        "events": 0,
        "matches": 0,
        "team_years": 0,
        "team_events": 0,
        "team_matches": 0,
        "errors": [],
    }
    
    print(f"\n{'='*60}")
    print(f"Processing FTC Season {season} (parallel, {max_workers} workers)")
    print(f"{'='*60}")
    
    # 1. Fetch all teams for this season
    print("\n[1/6] Fetching teams...")
    teams_data = get_teams(season, cache=cache)
    timer.log(f"Fetched {len(teams_data)} teams")
    
    # 2. Fetch all events for this season
    print("\n[2/6] Fetching events...")
    events_data, _ = get_events(season, cache=cache)
    timer.log(f"Fetched {len(events_data)} events")
    
    # 3. Process events IN PARALLEL
    print(f"\n[3/6] Processing {len(events_data)} events in parallel...")
    all_matches: List[Dict] = []
    all_team_events: List[Dict] = []
    all_rankings: List[Dict] = []
    event_team_map: Dict[str, List[int]] = {}
    team_matches: Dict[int, List[Dict]] = defaultdict(list)
    
    completed_count = 0
    
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        # Submit all events for processing
        future_to_event = {
            executor.submit(process_single_event, event, season, cache): event
            for event in events_data
        }
        
        # Collect results as they complete
        for future in as_completed(future_to_event):
            result = future.result()
            completed_count += 1
            
            if result["error"]:
                stats["errors"].append(result["error"])
                print(f"  Error: {result['error']}")
            else:
                event_key = result["event"]["key"]
                event_team_map[event_key] = result["event_teams"]
                all_team_events.extend(result["team_events"])
                all_rankings.extend(result["rankings"])
                
                for match in result["matches"]:
                    # Track matches per team
                    for team_num in [match.get("red_1"), match.get("red_2"), match.get("blue_1"), match.get("blue_2")]:
                        if team_num:
                            team_matches[team_num].append(match)
                    all_matches.append(match)
            
            if completed_count % 50 == 0:
                timer.log(f"Processed {completed_count}/{len(events_data)} events")
    
    timer.log(f"Processed all {len(events_data)} events, {len(all_matches)} matches")
    
    # Create team name lookup
    team_name_lookup = {team["team"]: team.get("name", f"Team {team['team']}") for team in teams_data}
    
    # Group matches by event for team-event record calculation
    event_matches: Dict[str, List[Dict]] = defaultdict(list)
    for match in all_matches:
        event_key = match.get("event")
        if event_key:
            event_matches[event_key].append(match)
    
    # Update team_events with team names and match records
    for te in all_team_events:
        team_num = te["team"]
        event_key = te["event"]
        
        # Set team name
        te["team_name"] = team_name_lookup.get(team_num, f"Team {team_num}")
        
        # Calculate match record for this team at this event
        event_match_list = event_matches.get(event_key, [])
        team_event_matches = [
            m for m in event_match_list
            if team_num in [m.get("red_1"), m.get("red_2"), m.get("blue_1"), m.get("blue_2")]
        ]
        
        wins, losses, ties, count = 0, 0, 0, 0
        qual_wins, qual_losses, qual_ties, qual_count = 0, 0, 0, 0
        
        for match in team_event_matches:
            if match.get("status") != MatchStatus.COMPLETED.value:
                continue
            
            red_teams = [match.get("red_1"), match.get("red_2")]
            blue_teams = [match.get("blue_1"), match.get("blue_2")]
            winner = match.get("winner")
            is_qual = match.get("comp_level") == CompLevel.QUAL.value
            
            if team_num in red_teams:
                if winner == MatchWinner.RED.value:
                    wins += 1
                    if is_qual:
                        qual_wins += 1
                elif winner == MatchWinner.BLUE.value:
                    losses += 1
                    if is_qual:
                        qual_losses += 1
                else:
                    ties += 1
                    if is_qual:
                        qual_ties += 1
            elif team_num in blue_teams:
                if winner == MatchWinner.BLUE.value:
                    wins += 1
                    if is_qual:
                        qual_wins += 1
                elif winner == MatchWinner.RED.value:
                    losses += 1
                    if is_qual:
                        qual_losses += 1
                else:
                    ties += 1
                    if is_qual:
                        qual_ties += 1
            
            count += 1
            if is_qual:
                qual_count += 1
        
        te["wins"] = wins
        te["losses"] = losses
        te["ties"] = ties
        te["count"] = count
        te["winrate"] = round(wins / count, 3) if count > 0 else 0
        te["qual_wins"] = qual_wins
        te["qual_losses"] = qual_losses
        te["qual_ties"] = qual_ties
        te["qual_count"] = qual_count
        te["qual_winrate"] = round(qual_wins / qual_count, 3) if qual_count > 0 else 0
    
    timer.log(f"Updated {len(all_team_events)} team-event records with names and stats")
    
    # 4. Calculate EPA and stats for each team (with progression history)
    print("\n[4/6] Calculating team statistics...")
    team_years_data: List[Dict] = []
    
    # Store EPA history for all teams (for creating team_matches later)
    all_team_epa_history: Dict[int, Dict[str, Dict[str, float]]] = {}
    
    for team in teams_data:
        team_num = team["team"]
        team_match_list = team_matches.get(team_num, [])
        
        # Calculate EPA with history for progression graphs
        epa_data, epa_history = calculate_epa_with_history(team_match_list, team_num)
        all_team_epa_history[team_num] = epa_history
        
        # Calculate record
        record = calculate_record(team_match_list, team_num)
        
        # Find events this team attended
        team_event_keys = [te["event"] for te in all_team_events if te["team"] == team_num]
        
        team_year = {
            "team": team_num,
            "year": season,
            "name": team.get("name", f"Team {team_num}"),
            "country": team.get("country"),
            "state": team.get("state"),
            "rookie_year": team.get("rookie_year"),
            "events_attended": len(team_event_keys),
            "event_keys": team_event_keys,
            **epa_data,
            **record,
        }
        
        team_years_data.append(team_year)
    
    # Sort by EPA and add rankings
    team_years_data.sort(key=lambda x: x.get("epa", 0), reverse=True)
    epa_list = [ty["epa"] for ty in team_years_data if ty.get("epa")]
    
    # Calculate norm_epa and unitless_epa
    if epa_list:
        epa_min = min(epa_list)
        epa_max_val = max(epa_list)
        epa_range = epa_max_val - epa_min if epa_max_val != epa_min else 1
    
    for i, ty in enumerate(team_years_data):
        ty["total_epa_rank"] = i + 1
        ty["total_epa_percentile"] = round(1 - (i / len(team_years_data)), 4) if team_years_data else 0
        
        # Calculate unitless_epa (normalized to 1500 scale like Elo)
        epa = ty.get("epa", 20)
        if epa_list and len(epa_list) > 1:
            # Scale EPA to 1500 +/- 300 range (like Elo)
            import statistics
            epa_mean = statistics.mean(epa_list)
            epa_sd = statistics.stdev(epa_list) if len(epa_list) > 1 else 1
            ty["unitless_epa"] = round(1500 + ((epa - epa_mean) / epa_sd) * 150, 0) if epa_sd > 0 else 1500
            
            # Calculate norm_epa (percentile-based normalization to 1500 scale)
            percentile = 1 - (i / len(team_years_data))
            ty["norm_epa"] = round(1200 + (percentile * 600), 0)  # Range 1200-1800
        else:
            ty["unitless_epa"] = 1500
            ty["norm_epa"] = 1500
    
    timer.log(f"Calculated stats for {len(team_years_data)} teams")
    
    # 5. Calculate year-level statistics
    print("\n[5/6] Calculating year statistics...")
    scores = []
    auto_scores = []
    teleop_scores = []
    endgame_scores = []
    
    for match in all_matches:
        if match.get("status") == MatchStatus.COMPLETED.value:
            red_score = match.get("red_score") or 0
            blue_score = match.get("blue_score") or 0
            scores.extend([red_score, blue_score])
            
            red_bd = match.get("red_score_breakdown", {}) or {}
            blue_bd = match.get("blue_score_breakdown", {}) or {}
            
            # Only add non-None values to avoid statistics errors
            red_auto = red_bd.get("auto_points")
            blue_auto = blue_bd.get("auto_points")
            if red_auto is not None:
                auto_scores.append(red_auto)
            if blue_auto is not None:
                auto_scores.append(blue_auto)
            
            red_teleop = red_bd.get("teleop_points")
            blue_teleop = blue_bd.get("teleop_points")
            if red_teleop is not None:
                teleop_scores.append(red_teleop)
            if blue_teleop is not None:
                teleop_scores.append(blue_teleop)
            
            red_endgame = red_bd.get("endgame_points")
            blue_endgame = blue_bd.get("endgame_points")
            if red_endgame is not None:
                endgame_scores.append(red_endgame)
            if blue_endgame is not None:
                endgame_scores.append(blue_endgame)
    
    import statistics
    
    year_data = {
        "year": season,
        "team_count": len(teams_data),
        "event_count": len(events_data),
        "match_count": len(all_matches),
        "score_mean": round(statistics.mean(scores), 2) if scores else 0,
        "score_sd": round(statistics.stdev(scores), 2) if len(scores) > 1 else 0,
        "score_median": round(statistics.median(scores), 2) if scores else 0,
        "auto_mean": round(statistics.mean(auto_scores), 2) if auto_scores else 0,
        "teleop_mean": round(statistics.mean(teleop_scores), 2) if teleop_scores else 0,
        "endgame_mean": round(statistics.mean(endgame_scores), 2) if endgame_scores else 0,
        "epa_mean": round(statistics.mean([ty["epa"] for ty in team_years_data]), 2) if team_years_data else 0,
        "epa_99p": round(sorted([ty["epa"] for ty in team_years_data], reverse=True)[int(len(team_years_data) * 0.01)] if team_years_data else 0, 2),
        "epa_90p": round(sorted([ty["epa"] for ty in team_years_data], reverse=True)[int(len(team_years_data) * 0.10)] if team_years_data else 0, 2),
        "epa_75p": round(sorted([ty["epa"] for ty in team_years_data], reverse=True)[int(len(team_years_data) * 0.25)] if team_years_data else 0, 2),
        "epa_25p": round(sorted([ty["epa"] for ty in team_years_data], reverse=True)[int(len(team_years_data) * 0.75)] if team_years_data else 0, 2),
        # Auto percentiles
        "auto_epa_99p": round(sorted([ty.get("auto_epa", 0) or 0 for ty in team_years_data], reverse=True)[int(len(team_years_data) * 0.01)] if team_years_data else 0, 2),
        "auto_epa_90p": round(sorted([ty.get("auto_epa", 0) or 0 for ty in team_years_data], reverse=True)[int(len(team_years_data) * 0.10)] if team_years_data else 0, 2),
        "auto_epa_75p": round(sorted([ty.get("auto_epa", 0) or 0 for ty in team_years_data], reverse=True)[int(len(team_years_data) * 0.25)] if team_years_data else 0, 2),
        "auto_epa_25p": round(sorted([ty.get("auto_epa", 0) or 0 for ty in team_years_data], reverse=True)[int(len(team_years_data) * 0.75)] if team_years_data else 0, 2),
        # Teleop percentiles
        "teleop_epa_99p": round(sorted([ty.get("teleop_epa", 0) or 0 for ty in team_years_data], reverse=True)[int(len(team_years_data) * 0.01)] if team_years_data else 0, 2),
        "teleop_epa_90p": round(sorted([ty.get("teleop_epa", 0) or 0 for ty in team_years_data], reverse=True)[int(len(team_years_data) * 0.10)] if team_years_data else 0, 2),
        "teleop_epa_75p": round(sorted([ty.get("teleop_epa", 0) or 0 for ty in team_years_data], reverse=True)[int(len(team_years_data) * 0.25)] if team_years_data else 0, 2),
        "teleop_epa_25p": round(sorted([ty.get("teleop_epa", 0) or 0 for ty in team_years_data], reverse=True)[int(len(team_years_data) * 0.75)] if team_years_data else 0, 2),
        # Endgame percentiles
        "endgame_epa_99p": round(sorted([ty.get("endgame_epa", 0) or 0 for ty in team_years_data], reverse=True)[int(len(team_years_data) * 0.01)] if team_years_data else 0, 2),
        "endgame_epa_90p": round(sorted([ty.get("endgame_epa", 0) or 0 for ty in team_years_data], reverse=True)[int(len(team_years_data) * 0.10)] if team_years_data else 0, 2),
        "endgame_epa_75p": round(sorted([ty.get("endgame_epa", 0) or 0 for ty in team_years_data], reverse=True)[int(len(team_years_data) * 0.25)] if team_years_data else 0, 2),
        "endgame_epa_25p": round(sorted([ty.get("endgame_epa", 0) or 0 for ty in team_years_data], reverse=True)[int(len(team_years_data) * 0.75)] if team_years_data else 0, 2),
    }
    
    timer.log("Calculated year statistics")
    
    # 5.5 Add match predictions using team EPAs
    print("  Adding match predictions...")
    team_epas = {ty["team"]: ty["epa"] for ty in team_years_data}
    score_sd = year_data["score_sd"] if year_data["score_sd"] > 0 else 50
    add_match_predictions(all_matches, team_epas, score_sd)
    timer.log(f"Added predictions to {len(all_matches)} matches")
    
    # 5.6 Update team_events with EPA progression data
    print("  Updating team events with EPA data...")
    # Build a dict for quick event lookup
    event_matches_dict: Dict[str, List[Dict]] = defaultdict(list)
    for match in all_matches:
        event_matches_dict[match.get("event")].append(match)
    
    for te in all_team_events:
        team_num = te["team"]
        event_key = te["event"]
        epa_history = all_team_epa_history.get(team_num, {})
        
        # Get matches for this team at this event, sorted by time
        event_team_matches = sorted(
            [m for m in event_matches_dict.get(event_key, [])
             if team_num in [m.get("red_1"), m.get("red_2"), m.get("blue_1"), m.get("blue_2")]],
            key=lambda m: m.get("time", 0)
        )
        
        if event_team_matches:
            # Get EPA at start and end of event
            first_match_key = event_team_matches[0].get("key")
            last_match_key = event_team_matches[-1].get("key")
            
            first_epa_data = epa_history.get(first_match_key, {})
            last_epa_data = epa_history.get(last_match_key, {})
            
            te["epa_start"] = first_epa_data.get("epa", 20.0)
            te["epa"] = last_epa_data.get("post_epa", te.get("epa", 20.0))
            te["epa_end"] = last_epa_data.get("post_epa", 20.0)
            te["epa_diff"] = round(te["epa_end"] - te["epa_start"], 2)
            te["epa_max"] = max([epa_history.get(m.get("key"), {}).get("post_epa", 0) for m in event_team_matches] or [20.0])
            
            # Component EPAs
            te["auto_epa"] = last_epa_data.get("post_auto_epa", None)
            te["teleop_epa"] = last_epa_data.get("post_teleop_epa", None)
            te["endgame_epa"] = last_epa_data.get("post_endgame_epa", None)
            
            # Get pre-elim EPA (EPA after last qual match)
            qual_matches = [m for m in event_team_matches if m.get("comp_level") == CompLevel.QUAL.value]
            if qual_matches:
                last_qual_key = qual_matches[-1].get("key")
                last_qual_epa = epa_history.get(last_qual_key, {})
                te["epa_pre_elim"] = last_qual_epa.get("post_epa", te["epa_end"])
            else:
                te["epa_pre_elim"] = te["epa_end"]
    
    # 5.6.1 Calculate unitless_epa and norm_epa for team_events
    # Use the same EPA statistics from team_years
    if epa_list and len(epa_list) > 1:
        epa_mean = statistics.mean(epa_list)
        epa_sd = statistics.stdev(epa_list) if len(epa_list) > 1 else 1
        
        for te in all_team_events:
            te_epa = te.get("epa", 20)
            if epa_sd > 0:
                te["unitless_epa"] = round(1500 + ((te_epa - epa_mean) / epa_sd) * 150, 0)
            else:
                te["unitless_epa"] = 1500
            
            # Calculate norm_epa based on percentile within all team_events
            # Find rank among all team_events by EPA
            te_rank = sum(1 for other in all_team_events if other.get("epa", 0) > te_epa)
            te_percentile = 1 - (te_rank / max(len(all_team_events), 1))
            te["norm_epa"] = round(1200 + (te_percentile * 600), 0)
    else:
        for te in all_team_events:
            te["unitless_epa"] = 1500
            te["norm_epa"] = 1500
    
    timer.log(f"Updated {len(all_team_events)} team events with EPA data")
    
    # 5.7 Create team_matches data with EPA progression
    print("  Creating team matches with EPA progression...")
    all_team_matches: List[Dict] = []
    
    for match in all_matches:
        match_key = match.get("key")
        event_key = match.get("event")
        match_time = match.get("time", 0)
        match_week = match.get("week", 0)
        comp_level = match.get("comp_level")
        match_status = match.get("status", "Upcoming")
        is_elim = comp_level not in ["qm", CompLevel.QUAL.value] if comp_level else False
        
        # Get teams in this match
        for alliance, team_keys in [("red", ["red_1", "red_2"]), ("blue", ["blue_1", "blue_2"])]:
            for team_key in team_keys:
                team_num = match.get(team_key)
                if not team_num:
                    continue
                
                # Get team's EPA history for this match
                epa_history = all_team_epa_history.get(team_num, {})
                match_epa = epa_history.get(match_key, {})
                
                # Use progression EPA if available, otherwise fall back to final EPA
                pre_epa = match_epa.get("epa", team_epas.get(team_num, 20.0))
                post_epa = match_epa.get("post_epa", pre_epa)
                
                team_match = {
                    "team": team_num,
                    "year": season,
                    "event": event_key,
                    "match": match_key,
                    "alliance": alliance,
                    "time": match_time,
                    "week": match_week,
                    "elim": is_elim,
                    "dq": False,
                    "surrogate": False,
                    "status": match_status,
                    "epa": round(pre_epa, 2),
                    "auto_epa": match_epa.get("post_auto_epa"),
                    "teleop_epa": match_epa.get("post_teleop_epa"),
                    "endgame_epa": match_epa.get("post_endgame_epa"),
                    "post_epa": round(post_epa, 2),
                }
                
                all_team_matches.append(team_match)
    
    timer.log(f"Created {len(all_team_matches)} team matches")
    
    # 6. Write everything to database
    print("\n[6/6] Writing to database...")
    
    # Prepare team data with active flag
    for team in teams_data:
        team["active"] = True
    
    stats["teams"] = write_teams(teams_data)
    timer.log(f"Wrote {stats['teams']} teams")
    
    stats["events"] = write_events(events_data)
    timer.log(f"Wrote {stats['events']} events")
    
    stats["matches"] = write_matches(all_matches)
    timer.log(f"Wrote {stats['matches']} matches")
    
    stats["team_years"] = write_team_years(team_years_data)
    timer.log(f"Wrote {stats['team_years']} team years")
    
    stats["team_events"] = write_team_events(all_team_events)
    timer.log(f"Wrote {stats['team_events']} team events")
    
    stats["team_matches"] = write_team_matches(all_team_matches)
    timer.log(f"Wrote {stats['team_matches']} team matches")
    
    write_year(year_data)
    timer.log("Wrote year statistics")
    
    write_rankings(f"{season}_all", all_rankings)
    timer.log(f"Wrote {len(all_rankings)} rankings")
    
    # Update metadata
    write_metadata(f"season_{season}", {
        "last_updated": datetime.utcnow().isoformat(),
        "stats": stats,
    })
    
    print(f"\n{'='*60}")
    print(f"Season {season} processing complete!")
    print(f"  Teams: {stats['teams']}")
    print(f"  Events: {stats['events']}")
    print(f"  Matches: {stats['matches']}")
    print(f"  Team Years: {stats['team_years']}")
    print(f"  Team Matches: {stats['team_matches']}")
    print(f"  Errors: {len(stats['errors'])}")
    print(f"{'='*60}")
    
    return stats


def process_all_seasons(start_year: int = 2022, end_year: int = 2024, cache: bool = True, reset: bool = False) -> List[Dict]:
    """
    Process multiple FTC seasons
    
    Args:
        start_year: First season to process
        end_year: Last season to process
        cache: Whether to use cached API responses
        reset: If True, reset the database before processing
    """
    # Initialize/reset the database
    if reset:
        print("\n[DB] Resetting database...")
        reset_db()
    else:
        print("\n[DB] Initializing database...")
        init_db()
    
    results = []
    
    for year in range(start_year, end_year + 1):
        try:
            result = process_season(year, cache=cache)
            results.append(result)
        except Exception as e:
            print(f"Error processing season {year}: {e}")
            import traceback
            traceback.print_exc()
            results.append({"season": year, "error": str(e)})
    
    return results
    
    return results


def update_current_season(cache: bool = False) -> Dict[str, Any]:
    """
    Update data for the current season
    
    This is meant for periodic updates to refresh live data.
    """
    from src.constants import CURR_YEAR
    return process_season(CURR_YEAR, cache=cache, full_refresh=False)


def update_live_events(season: int = None) -> Dict[str, Any]:
    """
    Update only ongoing/recent events for faster live updates.
    
    This function:
    1. Finds events that are currently ongoing or recently completed
    2. Re-fetches match data for those events only
    3. Recalculates EPA and updates the database
    
    This is much faster than re-processing the entire season.
    """
    from datetime import datetime, timedelta
    from src.constants import CURR_YEAR
    from src.db.read import get_events
    
    if season is None:
        season = CURR_YEAR
    
    timer = Timer()
    
    print(f"\n{'='*60}")
    print(f"Updating Live Events for Season {season}")
    print(f"{'='*60}")
    
    # Get all events for this season
    events, _ = get_events(season=season)
    if not events:
        print("No events found")
        return {"updated_events": 0}
    
    # Find ongoing events
    now = datetime.now()
    ongoing_events = []
    
    for event in events:
        status = event.get("status") or event.status if hasattr(event, "status") else None
        # Check if event is ongoing
        if status == EventStatus.ONGOING.value:
            ongoing_events.append(event)
            continue
        
        # Also check events that ended in the last 6 hours (in case status wasn't updated)
        event_end = event.get("end_date") if isinstance(event, dict) else getattr(event, "end_date", None)
        if event_end:
            try:
                if isinstance(event_end, str):
                    end_dt = datetime.fromisoformat(event_end.replace("Z", "+00:00"))
                else:
                    end_dt = event_end
                if now - end_dt < timedelta(hours=6):
                    ongoing_events.append(event)
            except (ValueError, TypeError):
                pass
    
    if not ongoing_events:
        print("No ongoing events found")
        return {"updated_events": 0}
    
    print(f"Found {len(ongoing_events)} ongoing events")
    
    updated_count = 0
    for event in ongoing_events:
        event_key = event.get("key") if isinstance(event, dict) else event.key
        event_code = event_key.split("_")[1] if "_" in event_key else event_key
        
        try:
            print(f"  Updating event: {event_key}")
            
            # Re-fetch match data for this event
            matches, _ = get_event_matches(season, event_code, cache=False)
            
            if matches:
                # Process and write matches
                for match in matches:
                    match["event"] = event_key
                    match["week"] = event.get("week") if isinstance(event, dict) else getattr(event, "week", 0)
                    if match.get("winner") and hasattr(match["winner"], "value"):
                        match["winner"] = match["winner"].value
                
                write_matches(matches)
                print(f"    Updated {len(matches)} matches")
                updated_count += 1
        except Exception as e:
            print(f"    Error updating {event_key}: {e}")
    
    timer.log(f"Updated {updated_count} events")
    
    # If any events were updated, recalculate EPA for affected teams
    if updated_count > 0:
        print("  Recalculating EPA for updated events...")
        # For now, trigger a full season recalc
        # In the future, this could be optimized to only recalculate affected teams
        process_season(season, cache=True, full_refresh=False)
    
    return {"updated_events": updated_count, "season": season}


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1:
        season = int(sys.argv[1])
        process_season(season, cache=False)
    else:
        # Process recent seasons
        process_all_seasons(2022, 2024, cache=False)
