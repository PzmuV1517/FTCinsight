import os
from pathlib import Path
from typing import List

# GLOBAL

PROD = os.getenv("PROD", "False") == "True"

# 8001 emulates the data server
BACKEND_URL = "https://api.ftcinsight.org" if PROD else "http://localhost:8001"

# DB - Local SQLite for development, PostgreSQL for production
DB_PATH = Path(__file__).parent.parent / "data" / "ftcinsight.db"

# Production: Use PostgreSQL (set via environment variable)
# Local: Use SQLite
if PROD:
    # Production PostgreSQL connection
    DB_USER = os.getenv("DB_USER", "")
    DB_PWD = os.getenv("DB_PWD", "")
    DB_HOST = os.getenv("DB_HOST", "")
    DB_NAME = os.getenv("DB_NAME", "ftcinsight")
    CONN_STR = f"postgresql://{DB_USER}:{DB_PWD}@{DB_HOST}/{DB_NAME}"
else:
    # Local SQLite for development
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    CONN_STR = f"sqlite:///{DB_PATH}"

# API

AUTH_KEY_BLACKLIST: List[str] = []

# CONFIG

CURR_YEAR = 2025  # FTC INTO THE DEEP season (2024-2025)
CURR_WEEK = 1

# FTC Season range (FTC data available from 2016 onward with good coverage)
MIN_YEAR = 2016
MAX_YEAR = 2026

# MISC

EPS = 1e-6
