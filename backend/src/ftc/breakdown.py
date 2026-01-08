"""
FTC Score Breakdown Module

Defines scoring breakdown keys and processing for FTC games.
This replaces the FRC-specific TBA breakdown module.
"""

from typing import Any, Dict, List

# FTC scoring breakdown keys by year
# These define the scoring components tracked for EPA calculations

# 2022 - FREIGHT FRENZY
KEYS_2022 = [
    "total_points",      # 0 - Total score (no foul)
    "auto_points",       # 1 - Autonomous points
    "teleop_points",     # 2 - TeleOp points  
    "endgame_points",    # 3 - Endgame points
    "auto_freight",      # 4 - Auto freight scored
    "teleop_freight",    # 5 - TeleOp freight scored
    "carousel_points",   # 6 - Carousel duck points
    "parking_points",    # 7 - Parking points
]

# 2023 - POWER PLAY
KEYS_2023 = [
    "total_points",      # 0 - Total score (no foul)
    "auto_points",       # 1 - Autonomous points
    "teleop_points",     # 2 - TeleOp points
    "endgame_points",    # 3 - Endgame points
    "auto_cones",        # 4 - Auto cones scored
    "teleop_cones",      # 5 - TeleOp cones scored
    "junctions_owned",   # 6 - Junctions owned
    "circuit_points",    # 7 - Circuit bonus
]

# 2024 - CENTERSTAGE
KEYS_2024 = [
    "total_points",      # 0 - Total score (no foul)
    "auto_points",       # 1 - Autonomous points
    "teleop_points",     # 2 - TeleOp points
    "endgame_points",    # 3 - Endgame points
    "auto_pixels",       # 4 - Auto pixels scored
    "teleop_pixels",     # 5 - TeleOp pixels scored
    "mosaic_points",     # 6 - Mosaic bonus points
    "drone_points",      # 7 - Drone landing points
    "backdrop_points",   # 8 - Backdrop points
]

# 2025 - INTO THE DEEP
KEYS_2025 = [
    "total_points",      # 0 - Total score (no foul)
    "auto_points",       # 1 - Autonomous points
    "teleop_points",     # 2 - TeleOp points
    "endgame_points",    # 3 - Endgame points
    "auto_samples",      # 4 - Auto samples scored
    "teleop_samples",    # 5 - TeleOp samples scored
    "specimen_points",   # 6 - Specimen points
    "basket_points",     # 7 - Basket points
    "ascent_points",     # 8 - Ascent/climb points
]

# 2026 - Current season (placeholder)
KEYS_2026 = [
    "total_points",      # 0 - Total score (no foul)
    "auto_points",       # 1 - Autonomous points
    "teleop_points",     # 2 - TeleOp points
    "endgame_points",    # 3 - Endgame points
]

# Default keys for unknown years
DEFAULT_KEYS = [
    "total_points",
    "auto_points", 
    "teleop_points",
    "endgame_points",
]

# Mapping of year to keys
all_keys: Dict[int, List[str]] = {
    2022: KEYS_2022,
    2023: KEYS_2023,
    2024: KEYS_2024,
    2025: KEYS_2025,
    2026: KEYS_2026,
}

def get_keys(year: int) -> List[str]:
    """Get scoring breakdown keys for a given year"""
    return all_keys.get(year, DEFAULT_KEYS)


def get_num_keys(year: int) -> int:
    """Get number of scoring components for a given year"""
    return len(get_keys(year))


def empty_breakdown(year: int) -> List[float]:
    """Return an empty breakdown array for a given year"""
    return [0.0] * len(get_keys(year))


def parse_ftc_score(score_data: Dict[str, Any], year: int) -> Dict[str, float]:
    """
    Parse FTC score data into a standardized breakdown format.
    
    Args:
        score_data: Raw score data from FTC API
        year: Season year
    
    Returns:
        Dictionary with standardized scoring breakdown
    """
    keys = get_keys(year)
    breakdown = {}
    
    # Always populate base keys
    breakdown["total_points"] = score_data.get("totalPointsNp", score_data.get("totalPoints", 0))
    breakdown["auto_points"] = score_data.get("autoPoints", 0)
    breakdown["teleop_points"] = score_data.get("dcPoints", score_data.get("teleopPoints", 0))
    breakdown["endgame_points"] = score_data.get("endgamePoints", 0)
    
    # Year-specific components
    if year == 2024:
        breakdown["auto_pixels"] = score_data.get("autoPixels", 0)
        breakdown["teleop_pixels"] = score_data.get("dcPixels", 0)
        breakdown["mosaic_points"] = score_data.get("mosaicPoints", 0)
        breakdown["drone_points"] = score_data.get("dronePoints", 0)
        breakdown["backdrop_points"] = score_data.get("backdropPoints", 0)
    elif year == 2025:
        breakdown["auto_samples"] = score_data.get("autoSamplePoints", 0)
        breakdown["teleop_samples"] = score_data.get("dcSamplePoints", 0)
        breakdown["specimen_points"] = score_data.get("specimenPoints", 0)
        breakdown["basket_points"] = score_data.get("basketPoints", 0)
        breakdown["ascent_points"] = score_data.get("ascentPoints", 0)
    
    return breakdown


def breakdown_to_array(breakdown: Dict[str, float], year: int) -> List[float]:
    """Convert breakdown dict to array matching keys order"""
    keys = get_keys(year)
    return [breakdown.get(key, 0.0) for key in keys]


def array_to_breakdown(arr: List[float], year: int) -> Dict[str, float]:
    """Convert array to breakdown dict"""
    keys = get_keys(year)
    return {key: arr[i] if i < len(arr) else 0.0 for i, key in enumerate(keys)}
