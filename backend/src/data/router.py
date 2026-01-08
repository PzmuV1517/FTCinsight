"""
FTC Insight Data Router

FastAPI router for data processing endpoints.
"""

import requests
from fastapi import APIRouter, BackgroundTasks

from src.constants import BACKEND_URL, CURR_YEAR
from src.data.main import reset_all_years, update_curr_year, process_single_season

data_router = APIRouter()
site_router = APIRouter()


@data_router.get("/")
async def read_root():
    return {"name": "FTC Data Router"}


@data_router.get("/reset_all_years")
async def reset_all_years_endpoint():
    """Reset and rebuild all historical data"""
    reset_all_years()
    return {"status": "success"}


@data_router.get("/reset_curr_year")
async def reset_curr_year_endpoint():
    """Full refresh of current season data"""
    update_curr_year(partial=False)
    return {"status": "success"}


@data_router.get("/update_curr_year")
async def update_curr_year_endpoint():
    """Incremental update of current season data"""
    update_curr_year(partial=True)
    return {"status": "success"}


@data_router.get("/process_season/{year}")
async def process_season_endpoint(year: int):
    """Process a specific season"""
    result = process_single_season(year, cache=True)
    return {"status": "success", "result": result}


def update_curr_year_background():
    """Background task to update current year"""
    requests.get(f"{BACKEND_URL}/v3/data/update_curr_year")


@site_router.get("/update_curr_year")
async def update_curr_year_site_endpoint(background_tasks: BackgroundTasks):
    """
    Trigger a background update of current season data.
    
    This endpoint checks if there's new data available before triggering
    the full update in the background.
    """
    # For FTC, we always trigger an update check
    # The pipeline handles caching internally
    background_tasks.add_task(update_curr_year_background)
    return {"status": "backgrounded"}
