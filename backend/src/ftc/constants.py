"""
FTC Constants

Constants specific to FTC data processing.
"""

# Placeholder team numbers (used to skip stats updates for dummy teams)
PLACEHOLDER_TEAMS = [0, 99999]

# FTC has 2-team alliances
ALLIANCE_SIZE = 2

# FTC scoring breakdown keys by year
# FTC games change annually, so we define the scoring components for each season
FTC_BREAKDOWN_KEYS = {
    2022: [
        "total_points",
        "auto_points",
        "teleop_points", 
        "endgame_points",
        "penalty_points",
    ],
    2023: [
        "total_points",
        "auto_points",
        "teleop_points",
        "endgame_points",
        "penalty_points",
    ],
    2024: [
        "total_points",
        "auto_points",
        "teleop_points",
        "endgame_points", 
        "penalty_points",
    ],
    2025: [
        "total_points",
        "auto_points",
        "teleop_points",
        "endgame_points",
        "penalty_points",
    ],
    2026: [
        "total_points",
        "auto_points",
        "teleop_points",
        "endgame_points",
        "penalty_points",
    ],
}

# Default breakdown keys
DEFAULT_BREAKDOWN_KEYS = [
    "total_points",
    "auto_points",
    "teleop_points",
    "endgame_points",
    "penalty_points",
]

def get_breakdown_keys(year: int):
    """Get scoring breakdown keys for a given year"""
    return FTC_BREAKDOWN_KEYS.get(year, DEFAULT_BREAKDOWN_KEYS)
