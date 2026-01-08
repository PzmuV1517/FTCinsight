"""
FTC Insight Data Processing Main Module

This module provides the main entry points for FTC data processing.
Uses the FTC Events API and Firebase Firestore for data storage.
"""

from typing import Dict, List, Optional

from src.constants import CURR_YEAR
from src.data.ftc_pipeline import (
    process_season,
    process_all_seasons,
    update_current_season,
    Timer,
)
from src.db.main import clean_db
from src.db.models import Team, TeamYear
from src.db.read import (
    get_num_years,
    get_team_years as get_team_years_db,
    get_teams as get_teams_db,
)
from src.db.write.main import update_teams as update_teams_db


def reset_all_years():
    """
    Reset and rebuild all data from scratch.
    
    This will:
    1. Clean the local database
    2. Fetch all teams and events from FTC API
    3. Process all seasons (2022-current)
    4. Store data in Firebase Firestore
    """
    timer = Timer()

    try:
        if get_num_years() > 0:
            print("Database already has data. Skipping reset.")
            return
    except Exception:
        pass

    clean_db()
    timer.log("Clean DB")

    # Process all seasons using FTC pipeline
    start_year = 2022  # FTC API data starts from 2022
    end_year = CURR_YEAR
    
    results = process_all_seasons(
        start_year=start_year,
        end_year=end_year,
        cache=True
    )
    timer.log(f"Processed {len(results)} seasons")
    
    for result in results:
        print(f"  Season {result['season']}: {result['teams_count']} teams, "
              f"{result['events_count']} events, {result['matches_count']} matches")


def update_curr_year(partial: bool = True):
    """
    Update the current year's data.
    
    Args:
        partial: If True, only fetch new/changed data.
                 If False, do a full refresh of the current season.
    """
    timer = Timer()

    result = update_current_season(cache=partial)
    timer.log(f"Updated season {result['season']}")
    
    print(f"  Teams: {result['teams_count']}")
    print(f"  Events: {result['events_count']}")
    print(f"  Matches: {result['matches_count']}")


def process_single_season(year: int, cache: bool = True) -> Dict:
    """
    Process a single season's data.
    
    Args:
        year: Season year to process
        cache: Whether to use cached data
    
    Returns:
        Dictionary with processing results
    """
    timer = Timer()
    
    result = process_season(season=year, cache=cache)
    timer.log(f"Processed season {year}")
    
    return result


def get_season_summary(year: int) -> Dict:
    """
    Get a summary of data for a given season.
    
    Args:
        year: Season year
    
    Returns:
        Dictionary with counts and summary stats
    """
    from src.firebase.storage import read_year, read_teams, read_events
    
    year_data = read_year(year)
    teams = read_teams(year=year)
    events = read_events(year=year)
    
    return {
        "year": year,
        "teams_count": len(teams) if teams else 0,
        "events_count": len(events) if events else 0,
        "year_data": year_data,
    }
