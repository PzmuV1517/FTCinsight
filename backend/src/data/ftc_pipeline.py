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
    
    epa = prior_epa
    auto_epa = prior_epa * 0.3
    teleop_epa = prior_epa * 0.5
    endgame_epa = prior_epa * 0.2
    
    epa_max = epa
    epa_start = epa
    count = 0
    
    # Sort matches by time
    sorted_matches = sorted(matches, key=lambda m: m.get("time", 0))
    
    for match in sorted_matches:
        if match.get("status") != MatchStatus.COMPLETED.value:
            continue
        
        # Determine which alliance the team is on
        red_teams = [match.get("red_1"), match.get("red_2")]
        blue_teams = [match.get("blue_1"), match.get("blue_2")]
        
        if team_num in red_teams:
            alliance = "red"
            score = match.get("red_score", 0) or 0
            opp_score = match.get("blue_score", 0) or 0
            breakdown = match.get("red_score_breakdown", {})
        elif team_num in blue_teams:
            alliance = "blue"
            score = match.get("blue_score", 0) or 0
            opp_score = match.get("red_score", 0) or 0
            breakdown = match.get("blue_score_breakdown", {})
        else:
            continue
        
        # Expected score based on current EPA
        expected_score = epa * 2  # Two teams per alliance
        
        # Actual margin
        actual_margin = score - opp_score
        expected_margin = 0  # Start at 0 expected margin
        
        # Update EPA based on performance
        margin_error = actual_margin - expected_margin
        epa_update = k_factor * (score / 2 - epa)  # Per-robot contribution
        
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
        
        count += 1
    
    return {
        "epa": round(epa, 2),
        "auto_epa": round(auto_epa, 2),
        "teleop_epa": round(teleop_epa, 2),
        "endgame_epa": round(endgame_epa, 2),
        "epa_max": round(epa_max, 2),
        "epa_start": round(epa_start, 2),
        "count": count,
    }


def calculate_record(matches: List[Dict], team_num: int) -> Dict[str, int]:
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
    """Determine the status of an event based on its matches"""
    if not matches:
        return EventStatus.UPCOMING.value
    
    completed = sum(1 for m in matches if m.get("status") == MatchStatus.COMPLETED.value)
    total = len(matches)
    
    # Check if playoffs have finished
    playoff_matches = [m for m in matches if m.get("comp_level") != CompLevel.QUAL.value]
    finals = [m for m in playoff_matches if m.get("comp_level") == CompLevel.FINAL.value]
    
    if completed == 0:
        return EventStatus.UPCOMING.value
    elif completed < total or not finals:
        return EventStatus.ONGOING.value
    else:
        return EventStatus.COMPLETED.value


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
        
        # Create team-event records
        for team_num in event_teams:
            result["team_events"].append({
                "team": team_num,
                "event": event_key,
                "year": season,
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
        event["team_count"] = len(event_teams)
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
    
    # 4. Calculate EPA and stats for each team
    print("\n[4/6] Calculating team statistics...")
    team_years_data: List[Dict] = []
    
    for team in teams_data:
        team_num = team["team"]
        team_match_list = team_matches.get(team_num, [])
        
        # Calculate EPA
        epa_data = calculate_epa(team_match_list, team_num)
        
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
    for i, ty in enumerate(team_years_data):
        ty["epa_rank"] = i + 1
        ty["epa_percentile"] = round(1 - (i / len(team_years_data)), 3) if team_years_data else 0
    
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
            
            red_bd = match.get("red_score_breakdown", {})
            blue_bd = match.get("blue_score_breakdown", {})
            
            auto_scores.extend([red_bd.get("auto_points", 0), blue_bd.get("auto_points", 0)])
            teleop_scores.extend([red_bd.get("teleop_points", 0), blue_bd.get("teleop_points", 0)])
            endgame_scores.extend([red_bd.get("endgame_points", 0), blue_bd.get("endgame_points", 0)])
    
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
    }
    
    timer.log("Calculated year statistics")
    
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


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1:
        season = int(sys.argv[1])
        process_season(season, cache=False)
    else:
        # Process recent seasons
        process_all_seasons(2022, 2024, cache=False)
