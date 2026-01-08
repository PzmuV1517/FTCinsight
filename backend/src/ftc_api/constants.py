import os
import base64
from typing import Dict, List

# Load .env file if present
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

# FTC API Configuration
FTC_API_USERNAME = os.getenv("FTC_API_USERNAME", "")
FTC_API_TOKEN = os.getenv("FTC_API_TOKEN", "")
FTC_API_BASE_URL = os.getenv("FTC_API_BASE_URL", "https://ftc-api.firstinspires.org")

# Generate the authorization header value
def get_auth_header() -> str:
    """Generate Base64 encoded authorization header for FTC Events API"""
    if not FTC_API_USERNAME or not FTC_API_TOKEN:
        raise ValueError("FTC API credentials not configured. Set FTC_API_USERNAME and FTC_API_TOKEN environment variables.")
    credentials = f"{FTC_API_USERNAME}:{FTC_API_TOKEN}"
    encoded = base64.b64encode(credentials.encode()).decode()
    return f"Basic {encoded}"


# GEOGRAPHY (same as before, used for state normalization)

USA_MAPPING: Dict[str, str] = {
    "Alabama": "AL",
    "Alaska": "AK",
    "American Samoa": "AS",
    "Arizona": "AZ",
    "Arkansas": "AR",
    "California": "CA",
    "Colorado": "CO",
    "Connecticut": "CT",
    "Delaware": "DE",
    "District of Columbia": "DC",
    "Florida": "FL",
    "Georgia": "GA",
    "Guam": "GU",
    "Hawaii": "HI",
    "Idaho": "ID",
    "Illinois": "IL",
    "Indiana": "IN",
    "Iowa": "IA",
    "Kansas": "KS",
    "Kentucky": "KY",
    "Louisiana": "LA",
    "Maine": "ME",
    "Maryland": "MD",
    "Massachusetts": "MA",
    "Michigan": "MI",
    "Minnesota": "MN",
    "Mississippi": "MS",
    "Missouri": "MO",
    "Montana": "MT",
    "Nebraska": "NE",
    "Nevada": "NV",
    "New Hampshire": "NH",
    "New Jersey": "NJ",
    "New Mexico": "NM",
    "New York": "NY",
    "North Carolina": "NC",
    "North Dakota": "ND",
    "Northern Mariana Islands": "MP",
    "Ohio": "OH",
    "Oklahoma": "OK",
    "Oregon": "OR",
    "Pennsylvania": "PA",
    "Puerto Rico": "PR",
    "Rhode Island": "RI",
    "South Carolina": "SC",
    "South Dakota": "SD",
    "Tennessee": "TN",
    "Texas": "TX",
    "Utah": "UT",
    "Vermont": "VT",
    "Virgin Islands": "VI",
    "Virginia": "VA",
    "Washington": "WA",
    "West Virginia": "WV",
    "Wisconsin": "WI",
    "Wyoming": "WY",
}

CANADA_MAPPING: Dict[str, str] = {
    "Newfoundland": "NL",
    "Prince Edward Island": "PE",
    "Nova Scotia": "NS",
    "New Brunswick": "NB",
    "Québec": "QC",
    "Quebec": "QC",
    "Ontario": "ON",
    "Manitoba": "MB",
    "Saskatchewan": "SK",
    "Alberta": "AB",
    "British Columbia": "BC",
    "Yukon": "YT",
    "Northwest Territories": "NT",
    "Nunavut": "NU",
}

# FTC Region mappings
REGION_MAPPING: Dict[str, str] = {
    # Add FTC region codes as needed
}


# TEAMS - Placeholder teams for FTC (adjust as needed)
PLACEHOLDER_TEAMS = list(range(99970, 100000))


# BLACKLISTS

EVENT_BLACKLIST: List[str] = []

MATCH_BLACKLIST: List[str] = []

# FTC Event Type mappings
FTC_EVENT_TYPES = {
    "Scrimmage": "scrimmage",
    "LeagueMeet": "league_meet",
    "Qualifier": "qualifier",
    "LeagueTournament": "league_tournament",
    "Championship": "championship",
    "SuperQualifier": "super_qualifier",
    "RegionalChampionship": "regional_championship",
    "FIRSTChampionship": "first_championship",
    "OffSeason": "offseason",
    "Other": "other",
}

# FTC Game Names by season
FTC_GAMES = {
    2024: "INTO THE DEEP",
    2023: "CENTERSTAGE",
    2022: "POWERPLAY",
    2021: "FREIGHT FRENZY",
    2020: "ULTIMATE GOAL",
    2019: "SKYSTONE",
    2018: "ROVER RUCKUS",
    2017: "RELIC RECOVERY",
    2016: "VELOCITY VORTEX",
}
