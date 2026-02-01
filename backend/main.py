import asyncio
import platform
from contextlib import asynccontextmanager
from typing import Any, Callable

from dotenv import load_dotenv  # type: ignore

# from fastapi import APIRouter, Depends, FastAPI, Request, Security
# from fastapi.exceptions import HTTPException
from fastapi import APIRouter, FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from fastapi.security.api_key import APIKeyHeader
from pyinstrument import Profiler

load_dotenv()

# flake8: noqa E402
from src.api.router import router as api_router

# from src.constants import AUTH_KEY_BLACKLIST, CONN_STR, PROD
from src.constants import CONN_STR, PROD
from src.data.router import (
    data_router as data_data_router,
    site_router as data_site_router,
)
from src.site.router import router as site_router

# from src.utils.utils import is_uuid

"""
SETUP
"""

api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)

# Background task state
background_task = None
UPDATE_INTERVAL_SECONDS = 60  # Update every minute


async def periodic_update():
    """Background task that updates current season data periodically."""
    from src.data.ftc_pipeline import update_current_season
    
    while True:
        try:
            await asyncio.sleep(UPDATE_INTERVAL_SECONDS)
            print(f"[Auto-Update] Starting periodic update...")
            # Run in thread pool to not block async loop
            loop = asyncio.get_event_loop()
            await loop.run_in_executor(None, lambda: update_current_season(cache=False))
            print(f"[Auto-Update] Periodic update complete")
        except asyncio.CancelledError:
            print("[Auto-Update] Background task cancelled")
            break
        except Exception as e:
            print(f"[Auto-Update] Error during periodic update: {e}")
            # Continue running even if there's an error


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage application lifespan - start/stop background tasks."""
    global background_task
    
    # Startup: start background update task
    print("[Startup] Starting periodic update task (every 60 seconds)")
    background_task = asyncio.create_task(periodic_update())
    
    yield
    
    # Shutdown: cancel background task
    if background_task:
        print("[Shutdown] Cancelling periodic update task")
        background_task.cancel()
        try:
            await background_task
        except asyncio.CancelledError:
            pass


app = FastAPI(
    title="FTC Insight REST API",
    description="The REST API for FTC Insight - Data Analytics and Match Predictions for FIRST Tech Challenge. Please be nice to our servers! If you are looking to do large-scale data science projects, use the CSV exports on the GitHub repo.",
    version="3.0.0",
    # dependencies=[Security(get_api_key)],
    swagger_ui_parameters={"persistAuthorization": True},
    lifespan=lifespan,
)

# Removed CORS to enable website integrations
origins = [
    "http://localhost:3000",
    "https://ftcinsight.org",
    "https://www.ftcinsight.org",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


if not PROD:

    @app.middleware("http")
    async def profile_request(request: Request, call_next: Callable[[Any], Any]):
        profiling = request.query_params.get("profile", False)
        if profiling:
            profiler = Profiler(interval=0.001, async_mode="enabled")
            profiler.start()
            await call_next(request)
            profiler.stop()
            return HTMLResponse(profiler.output_html())
        else:
            return await call_next(request)


router = APIRouter()


@router.get("/")
async def read_root():
    return {"Hello": "World"}


@router.get("/info")
def get_info():
    return {
        "PROD": PROD,
        "CONN_STR": "REDACTED" if PROD else CONN_STR,
        "PYTHON_VERSION": platform.python_version(),
    }


app.include_router(router, include_in_schema=False)
app.include_router(api_router, prefix="/v3")
app.include_router(data_data_router, prefix="/v3/data", include_in_schema=False)
app.include_router(data_site_router, prefix="/v3/site", include_in_schema=False)
app.include_router(site_router, prefix="/v3/site", include_in_schema=False)
