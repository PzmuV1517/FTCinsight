"""
FTC Events API Data Reader

This module provides functions to read data from the FTC Events API
and transform it into the internal data structures used by FTC Insight.
"""

import time
from datetime import datetime
from typing import Dict, List, Optional, Tuple, cast

from src.ftc_api.main import get_ftc
from src.ftc_api.types import (
    EventDict,
    MatchDict,
    TeamDict,
    RankingDict,
    AllianceDict,
    BreakdownDict,
    empty_breakdown,
)
from src.ftc_api.constants import (
    USA_MAPPING,
    CANADA_MAPPING,
    EVENT_BLACKLIST,
    MATCH_BLACKLIST,
)
from src.ftc_api.breakdown import clean_breakdown
from src.types.enums import CompLevel, FTCEventType, MatchStatus, MatchWinner


def get_timestamp_from_str(date: str) -> int:
    """Convert date string to Unix timestamp"""
    try:
        return int(time.mktime(datetime.strptime(date.split("T")[0], "%Y-%m-%d").timetuple()))
    except Exception:
        return 0


def clean_state(state: Optional[str]) -> Optional[str]:
    """Normalize state/province names to abbreviations"""
    if state is None:
        return None
    
    if state in USA_MAPPING:
        return USA_MAPPING[state]
    elif state in CANADA_MAPPING:
        return CANADA_MAPPING[state]
    
    # Return as-is if already abbreviated or unknown
    return state if len(state) <= 3 else state


def get_api_status(cache: bool = False) -> Optional[Dict]:
    """Get FTC API status and current season info"""
    data, _ = get_ftc("", cache=cache)
    if type(data) is bool or data is None:
        return None
    return data


def get_season_summary(season: int, cache: bool = True) -> Optional[Dict]:
    """Get season summary including game name and team count"""
    data, _ = get_ftc(str(season), cache=cache)
    if type(data) is bool or data is None:
        return None
    return data


def get_teams(season: int, cache: bool = True) -> List[TeamDict]:
    """
    Get all teams for a given season
    
    FTC API paginates team listings, so we need to fetch all pages.
    """
    out: List[TeamDict] = []
    page = 1
    
    while True:
        url = f"{season}/teams?page={page}"
        data, _ = get_ftc(url, cache=cache)
        
        if type(data) is bool or data is None:
            break
            
        teams = data.get("teams", [])
        if not teams:
            break
            
        for team in teams:
            team_data: TeamDict = {
                "team": team["teamNumber"],
                "name": team.get("nameShort") or team.get("nameFull", ""),
                "rookie_year": team.get("rookieYear"),
                "country": team.get("country"),
                "state": clean_state(team.get("stateProv")),
                "city": team.get("city"),
                "school_name": team.get("schoolName"),
                "website": team.get("website"),
                "region": team.get("homeCMP"),
            }
            out.append(team_data)
        
        # Check if there are more pages
        page_current = data.get("pageCurrent", 1)
        page_total = data.get("pageTotal", 1)
        
        if page_current >= page_total:
            break
            
        page += 1
    
    return out


def get_team(team_number: int, season: int, cache: bool = True) -> Optional[TeamDict]:
    """Get a single team's information for a season"""
    url = f"{season}/teams?teamNumber={team_number}"
    data, _ = get_ftc(url, cache=cache)
    
    if type(data) is bool or data is None:
        return None
    
    teams = data.get("teams", [])
    if not teams:
        return None
    
    team = teams[0]
    return {
        "team": team["teamNumber"],
        "name": team.get("nameShort") or team.get("nameFull", ""),
        "rookie_year": team.get("rookieYear"),
        "country": team.get("country"),
        "state": clean_state(team.get("stateProv")),
        "city": team.get("city"),
        "school_name": team.get("schoolName"),
        "website": team.get("website"),
        "region": team.get("homeCMP"),
    }


def get_event_type(type_str: str) -> FTCEventType:
    """Convert FTC API event type string to FTCEventType enum"""
    type_mapping = {
        "Scrimmage": FTCEventType.SCRIMMAGE,
        "LeagueMeet": FTCEventType.LEAGUE_MEET,
        "Qualifier": FTCEventType.QUALIFIER,
        "LeagueTournament": FTCEventType.LEAGUE_TOURNAMENT,
        "Championship": FTCEventType.CHAMPIONSHIP,
        "SuperQualifier": FTCEventType.SUPER_QUALIFIER,
        "RegionalChampionship": FTCEventType.REGIONAL_CHAMPIONSHIP,
        "FIRSTChampionship": FTCEventType.FIRST_CHAMPIONSHIP,
        "OffSeason": FTCEventType.OFFSEASON,
        "Other": FTCEventType.OTHER,
    }
    return type_mapping.get(type_str, FTCEventType.OTHER)


def get_events(
    season: int, etag: Optional[str] = None, cache: bool = True
) -> Tuple[List[EventDict], Optional[str]]:
    """
    Get all events for a season
    """
    out: List[EventDict] = []
    url = f"{season}/events"
    data, new_etag = get_ftc(url, etag=etag, cache=cache)
    
    if type(data) is bool or data is None:
        return out, new_etag
    
    events = data.get("events", [])
    
    for event in events:
        event_code = event.get("code", "")
        key = f"{season}_{event_code}"
        
        # Skip blacklisted events
        if key in EVENT_BLACKLIST or event_code in EVENT_BLACKLIST:
            continue
        
        event_type = get_event_type(event.get("type", "Other"))
        
        # Calculate week (approximate based on date)
        start_date = event.get("dateStart", "")
        week = calculate_event_week(season, start_date)
        
        event_data: EventDict = {
            "year": season,
            "key": key,
            "event_code": event_code,
            "name": event.get("name", ""),
            "country": event.get("country"),
            "state": clean_state(event.get("stateprov")),
            "city": event.get("city"),
            "venue": event.get("venue"),
            "region": event.get("regionCode"),
            "league_code": event.get("leagueCode"),
            "start_date": start_date.split("T")[0] if start_date else "",
            "end_date": event.get("dateEnd", "").split("T")[0],
            "time": get_timestamp_from_str(start_date),
            "type": event_type,
            "week": week,
            "website": event.get("website"),
            "published": event.get("published", False),
        }
        
        out.append(event_data)
    
    return out, new_etag


def calculate_event_week(season: int, start_date: str) -> int:
    """
    Calculate the event week based on the date
    FTC season typically starts in September and runs through April
    """
    if not start_date:
        return 0
    
    try:
        event_date = datetime.strptime(start_date.split("T")[0], "%Y-%m-%d")
        # FTC kickoff is typically early September
        kickoff = datetime(season, 9, 1)
        
        if event_date < kickoff:
            # Pre-season event
            return 0
        
        delta = event_date - kickoff
        week = (delta.days // 7) + 1
        return min(week, 52)  # Cap at 52 weeks
    except Exception:
        return 0


def get_event_teams(
    season: int, event_code: str, etag: Optional[str] = None, cache: bool = True
) -> Tuple[List[int], Optional[str]]:
    """Get list of team numbers attending an event"""
    url = f"{season}/teams?eventCode={event_code}"
    data, new_etag = get_ftc(url, etag=etag, cache=cache)
    
    if type(data) is bool or data is None:
        return [], new_etag
    
    teams = data.get("teams", [])
    team_numbers = [team["teamNumber"] for team in teams]
    
    return team_numbers, new_etag


def get_event_schedule(
    season: int, 
    event_code: str, 
    tournament_level: str = "qual",
    cache: bool = True
) -> List[Dict]:
    """
    Get the match schedule for an event
    
    tournament_level: 'qual' or 'playoff'
    """
    url = f"{season}/schedule/{event_code}?tournamentLevel={tournament_level}"
    data, _ = get_ftc(url, cache=cache)
    
    if type(data) is bool or data is None:
        return []
    
    return data.get("schedule", [])


def get_event_matches(
    season: int,
    event_code: str,
    event_time: int,
    etag: Optional[str] = None,
    cache: bool = True,
) -> Tuple[List[MatchDict], Optional[str]]:
    """
    Get all matches and results for an event.
    Uses the match results endpoint for completed matches (has actual scores),
    and falls back to hybrid schedule for upcoming matches.
    """
    out: List[MatchDict] = []
    event_key = f"{season}_{event_code}"
    
    # First, try to get match results (completed matches with scores)
    match_results: Dict[Tuple[str, int], dict] = {}  # (level, match_num) -> result
    
    results_data, _ = get_ftc(f"{season}/matches/{event_code}", etag=etag, cache=cache)
    if results_data and isinstance(results_data, dict) and "matches" in results_data:
        for result in results_data["matches"]:
            level = result.get("tournamentLevel", "").upper()
            match_num = result.get("matchNumber", 0)
            series = result.get("series", 0)
            key = (level, series, match_num)
            match_results[key] = result
    
    # Get both qualification and playoff matches from schedule
    for tournament_level in ["qual", "playoff"]:
        url = f"{season}/schedule/{event_code}/{tournament_level}/hybrid"
        data, new_etag = get_ftc(url, etag=etag, cache=cache)
        
        if type(data) is bool or data is None:
            continue
        
        schedule = data.get("schedule", [])
        
        for match in schedule:
            match_number = match.get("matchNumber", 0)
            series = match.get("series", 1)
            
            # Determine comp level
            if tournament_level == "qual":
                comp_level = CompLevel.QUAL
                api_level = "QUALIFICATION"
            else:
                # FTC playoffs can be SF or F
                desc = match.get("description", "").lower()
                if "final" in desc:
                    comp_level = CompLevel.FINAL
                    api_level = "FINAL"
                else:
                    comp_level = CompLevel.SEMI
                    api_level = "SEMIFINAL"
            
            # Generate match key
            match_key = f"{event_key}_{comp_level.value}{series}m{match_number}"
            
            # Skip blacklisted matches
            if match_key in MATCH_BLACKLIST:
                continue
            
            # Get teams from the match
            teams = match.get("teams", [])
            red_teams = [t for t in teams if t.get("station", "").startswith("Red")]
            blue_teams = [t for t in teams if t.get("station", "").startswith("Blue")]
            
            if len(red_teams) < 2 or len(blue_teams) < 2:
                continue
            
            # Check if we have results for this match
            result_key = (api_level, series if tournament_level != "qual" else 0, match_number)
            result = match_results.get(result_key)
            
            # Get scores - prefer results endpoint, fall back to hybrid schedule
            if result:
                red_score = result.get("scoreRedFinal")
                blue_score = result.get("scoreBlueFinal")
                red_auto = result.get("scoreRedAuto", 0)
                blue_auto = result.get("scoreBlueAuto", 0)
                red_foul = result.get("scoreRedFoul", 0)
                blue_foul = result.get("scoreBlueFoul", 0)
                actual_time_str = result.get("actualStartTime")
                post_result_str = result.get("postResultTime")
            else:
                red_score = match.get("redScore")
                blue_score = match.get("blueScore")
                red_auto = 0
                blue_auto = 0
                red_foul = 0
                blue_foul = 0
                actual_time_str = None
                post_result_str = None
            
            # Determine match status
            status = MatchStatus.UPCOMING
            if red_score is not None and blue_score is not None and red_score >= 0 and blue_score >= 0:
                status = MatchStatus.COMPLETED
            
            # Determine winner
            winner = None
            if status == MatchStatus.COMPLETED:
                if red_score > blue_score:
                    winner = MatchWinner.RED
                elif blue_score > red_score:
                    winner = MatchWinner.BLUE
                else:
                    winner = MatchWinner.TIE
            
            # Parse scheduled time
            scheduled_time = match.get("startTime")
            match_time = get_timestamp_from_str(scheduled_time) if scheduled_time else event_time
            actual_time = get_timestamp_from_str(actual_time_str) if actual_time_str else None
            post_result_time = get_timestamp_from_str(post_result_str) if post_result_str else None
            
            # Get score breakdowns
            red_breakdown = empty_breakdown.copy()
            blue_breakdown = empty_breakdown.copy()
            
            # Set basic score info
            red_breakdown["score"] = red_score
            red_breakdown["auto"] = red_auto
            red_breakdown["foul"] = red_foul
            blue_breakdown["score"] = blue_score
            blue_breakdown["auto"] = blue_auto
            blue_breakdown["foul"] = blue_foul
            
            match_data: MatchDict = {
                "event": event_key,
                "key": match_key,
                "year": season,  # Required field for database
                "week": 0,  # FTC doesn't use weeks like FRC, default to 0
                "elim": comp_level != CompLevel.QUAL,  # True if playoff match
                "set_number": series,  # FTC uses series as set_number
                "comp_level": comp_level,
                "series": series,
                "match_number": match_number,
                "status": status,
                "red_1": red_teams[0].get("teamNumber", 0),
                "red_2": red_teams[1].get("teamNumber", 0) if len(red_teams) > 1 else 0,
                "red_surrogate_1": red_teams[0].get("surrogate", False),
                "red_surrogate_2": red_teams[1].get("surrogate", False) if len(red_teams) > 1 else False,
                "blue_1": blue_teams[0].get("teamNumber", 0),
                "blue_2": blue_teams[1].get("teamNumber", 0) if len(blue_teams) > 1 else 0,
                "blue_surrogate_1": blue_teams[0].get("surrogate", False),
                "blue_surrogate_2": blue_teams[1].get("surrogate", False) if len(blue_teams) > 1 else False,
                "winner": winner,
                "time": match_time,
                "actual_time": actual_time,
                "post_result_time": post_result_time,
                "red_score": red_score,
                "blue_score": blue_score,
                "red_score_breakdown": red_breakdown,
                "blue_score_breakdown": blue_breakdown,
            }
            
            out.append(match_data)
    
    return out, None


def get_event_scores(
    season: int,
    event_code: str,
    tournament_level: str = "qual",
    cache: bool = True,
) -> Dict[int, Tuple[BreakdownDict, BreakdownDict]]:
    """
    Get detailed score breakdowns for matches at an event
    
    Returns a dict mapping match_number to (red_breakdown, blue_breakdown)
    """
    url = f"{season}/scores/{event_code}/{tournament_level}"
    data, _ = get_ftc(url, cache=cache)
    
    result: Dict[int, Tuple[BreakdownDict, BreakdownDict]] = {}
    
    if type(data) is bool or data is None:
        return result
    
    match_scores = data.get("matchScores", [])
    
    for score in match_scores:
        match_number = score.get("matchNumber", 0)
        
        alliances = score.get("alliances", [])
        red_breakdown = empty_breakdown.copy()
        blue_breakdown = empty_breakdown.copy()
        
        for alliance in alliances:
            alliance_name = alliance.get("alliance", "")
            breakdown = clean_breakdown(season, alliance)
            
            if alliance_name.lower() == "red":
                red_breakdown = breakdown
            elif alliance_name.lower() == "blue":
                blue_breakdown = breakdown
        
        result[match_number] = (red_breakdown, blue_breakdown)
    
    return result


def get_event_rankings(
    season: int, event_code: str, etag: Optional[str] = None, cache: bool = True
) -> Tuple[Dict[int, int], Optional[str]]:
    """
    Get team rankings at an event
    
    Returns dict mapping team number to rank
    """
    out: Dict[int, int] = {}
    url = f"{season}/rankings/{event_code}"
    data, new_etag = get_ftc(url, etag=etag, cache=cache)
    
    if type(data) is bool or data is None:
        return out, new_etag
    
    rankings = data.get("rankings", [])
    
    for ranking in rankings:
        team_num = ranking.get("teamNumber", 0)
        rank = ranking.get("rank", 0)
        out[team_num] = rank
    
    return out, new_etag


def get_event_rankings_detailed(
    season: int, event_code: str, cache: bool = True
) -> List[RankingDict]:
    """Get detailed rankings for an event"""
    url = f"{season}/rankings/{event_code}"
    data, _ = get_ftc(url, cache=cache)
    
    if type(data) is bool or data is None:
        return []
    
    rankings = data.get("rankings", [])
    out: List[RankingDict] = []
    
    for r in rankings:
        ranking: RankingDict = {
            "team": r.get("teamNumber", 0),
            "rank": r.get("rank", 0),
            "wins": r.get("wins", 0),
            "losses": r.get("losses", 0),
            "ties": r.get("ties", 0),
            "qual_average": r.get("qualAverage"),
            "ranking_points": r.get("rankingPoints"),
            "tie_breaker_points": r.get("tieBreakerPoints"),
            "matches_played": r.get("matchesPlayed", 0),
            "dq": r.get("dq", 0),
            "sort_order_1": r.get("sortOrder1"),
            "sort_order_2": r.get("sortOrder2"),
            "sort_order_3": r.get("sortOrder3"),
            "sort_order_4": r.get("sortOrder4"),
            "sort_order_5": r.get("sortOrder5"),
            "sort_order_6": r.get("sortOrder6"),
        }
        out.append(ranking)
    
    return out


def get_event_alliances(
    season: int, event_code: str, etag: Optional[str] = None, cache: bool = True
) -> Tuple[Tuple[Dict[int, str], Dict[int, bool]], Optional[str]]:
    """
    Get alliance selection data for an event
    
    Returns:
        - alliance_dict: maps team number to alliance name
        - captain_dict: maps team number to whether they are captain
    """
    alliance_dict: Dict[int, str] = {}
    captain_dict: Dict[int, bool] = {}
    
    url = f"{season}/alliances/{event_code}"
    data, new_etag = get_ftc(url, etag=etag, cache=cache)
    
    if type(data) is bool or data is None:
        return (alliance_dict, captain_dict), new_etag
    
    alliances = data.get("alliances", [])
    
    for alliance in alliances:
        alliance_name = alliance.get("name", f"Alliance {alliance.get('number', 0)}")
        captain = alliance.get("captain")
        round1 = alliance.get("round1")
        round2 = alliance.get("round2")
        
        if captain:
            alliance_dict[captain] = alliance_name
            captain_dict[captain] = True
        
        if round1:
            alliance_dict[round1] = alliance_name
            captain_dict[round1] = False
        
        if round2:
            alliance_dict[round2] = alliance_name
            captain_dict[round2] = False
    
    return (alliance_dict, captain_dict), new_etag


def get_event_awards(
    season: int, event_code: str, cache: bool = True
) -> List[Dict]:
    """Get awards presented at an event"""
    url = f"{season}/awards/{event_code}"
    data, _ = get_ftc(url, cache=cache)
    
    if type(data) is bool or data is None:
        return []
    
    return data.get("awards", [])


def get_team_awards(
    season: int, team_number: int, cache: bool = True
) -> List[Dict]:
    """Get awards won by a team in a season"""
    url = f"{season}/awards/{team_number}"
    data, _ = get_ftc(url, cache=cache)
    
    if type(data) is bool or data is None:
        return []
    
    return data.get("awards", [])


def get_leagues(
    season: int, region_code: Optional[str] = None, cache: bool = True
) -> List[Dict]:
    """Get leagues for a season, optionally filtered by region"""
    url = f"{season}/leagues"
    if region_code:
        url += f"?regionCode={region_code}"
    
    data, _ = get_ftc(url, cache=cache)
    
    if type(data) is bool or data is None:
        return []
    
    return data.get("leagues", [])


def get_league_rankings(
    season: int, region_code: str, league_code: str, cache: bool = True
) -> List[RankingDict]:
    """Get cumulative league rankings"""
    url = f"{season}/leagues/rankings/{region_code}/{league_code}"
    data, _ = get_ftc(url, cache=cache)
    
    if type(data) is bool or data is None:
        return []
    
    rankings = data.get("rankings", [])
    out: List[RankingDict] = []
    
    for r in rankings:
        ranking: RankingDict = {
            "team": r.get("teamNumber", 0),
            "rank": r.get("rank", 0),
            "wins": r.get("wins", 0),
            "losses": r.get("losses", 0),
            "ties": r.get("ties", 0),
            "qual_average": r.get("qualAverage"),
            "ranking_points": r.get("rankingPoints"),
            "tie_breaker_points": r.get("tieBreakerPoints"),
            "matches_played": r.get("matchesPlayed", 0),
            "dq": r.get("dq", 0),
            "sort_order_1": r.get("sortOrder1"),
            "sort_order_2": r.get("sortOrder2"),
            "sort_order_3": r.get("sortOrder3"),
            "sort_order_4": r.get("sortOrder4"),
            "sort_order_5": r.get("sortOrder5"),
            "sort_order_6": r.get("sortOrder6"),
        }
        out.append(ranking)
    
    return out
