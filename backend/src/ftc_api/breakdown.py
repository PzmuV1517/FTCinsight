"""
FTC Score Breakdown Parser

This module handles parsing of game-specific score breakdowns for different FTC seasons.
Each FTC game has unique scoring elements that need to be extracted and normalized.
"""

from typing import Any, Dict, Optional, Union

from src.ftc_api.types import BreakdownDict, empty_breakdown


def clean_breakdown(season: int, alliance_data: Dict[str, Any]) -> BreakdownDict:
    """
    Clean and normalize score breakdown based on season
    
    Each season has different scoring elements, so we map them to generic comp_N fields
    while also extracting common elements like auto, teleop, and endgame points.
    """
    breakdown = empty_breakdown.copy()
    
    if not alliance_data:
        return breakdown
    
    # Common fields across most seasons
    breakdown["score"] = alliance_data.get("totalPoints") or alliance_data.get("totalPointsNp", 0)
    breakdown["auto_points"] = alliance_data.get("autoPoints", 0)
    breakdown["teleop_points"] = alliance_data.get("dcPoints") or alliance_data.get("teleopPoints", 0)
    breakdown["endgame_points"] = alliance_data.get("endgamePoints", 0)
    breakdown["penalty_points_committed"] = alliance_data.get("penaltyPointsCommitted", 0)
    
    # Season-specific breakdown parsing
    if season >= 2024:
        # INTO THE DEEP (2024-2025 season)
        breakdown = parse_into_the_deep(breakdown, alliance_data)
    elif season == 2023:
        # CENTERSTAGE (2023-2024 season)
        breakdown = parse_centerstage(breakdown, alliance_data)
    elif season == 2022:
        # POWERPLAY (2022-2023 season)
        breakdown = parse_powerplay(breakdown, alliance_data)
    elif season == 2021:
        # FREIGHT FRENZY (2021-2022 season)
        breakdown = parse_freight_frenzy(breakdown, alliance_data)
    elif season == 2020:
        # ULTIMATE GOAL (2020-2021 season)
        breakdown = parse_ultimate_goal(breakdown, alliance_data)
    elif season == 2019:
        # SKYSTONE (2019-2020 season)
        breakdown = parse_skystone(breakdown, alliance_data)
    
    return breakdown


def parse_into_the_deep(breakdown: BreakdownDict, data: Dict[str, Any]) -> BreakdownDict:
    """
    Parse INTO THE DEEP (2024-2025) scoring breakdown
    
    Scoring elements:
    - Autonomous: Net samples, baskets, ascent
    - TeleOp: Net samples, baskets
    - Endgame: Ascent levels (Level 1, 2, 3)
    """
    # Auto components
    breakdown["comp_1"] = data.get("autoSampleNet", 0)  # Samples in net (auto)
    breakdown["comp_2"] = data.get("autoSampleLow", 0)  # Low basket (auto)
    breakdown["comp_3"] = data.get("autoSampleHigh", 0)  # High basket (auto)
    breakdown["comp_4"] = data.get("autoSpecimenLow", 0)  # Low chamber specimen (auto)
    breakdown["comp_5"] = data.get("autoSpecimenHigh", 0)  # High chamber specimen (auto)
    
    # TeleOp components
    breakdown["comp_6"] = data.get("dcSampleNet", 0)  # Net samples (teleop)
    breakdown["comp_7"] = data.get("dcSampleLow", 0)  # Low basket (teleop)
    breakdown["comp_8"] = data.get("dcSampleHigh", 0)  # High basket (teleop)
    breakdown["comp_9"] = data.get("dcSpecimenLow", 0)  # Low chamber (teleop)
    breakdown["comp_10"] = data.get("dcSpecimenHigh", 0)  # High chamber (teleop)
    
    # Endgame - Ascent
    breakdown["comp_11"] = data.get("endgameAscent1", 0)  # Robot 1 ascent level
    breakdown["comp_12"] = data.get("endgameAscent2", 0)  # Robot 2 ascent level
    
    # Parking
    breakdown["comp_13"] = data.get("autoPark1", False)  # Robot 1 auto park
    breakdown["comp_14"] = data.get("autoPark2", False)  # Robot 2 auto park
    
    return breakdown


def parse_centerstage(breakdown: BreakdownDict, data: Dict[str, Any]) -> BreakdownDict:
    """
    Parse CENTERSTAGE (2023-2024) scoring breakdown
    
    Scoring elements:
    - Autonomous: Pixel placement, purple/yellow pixels, backstage
    - TeleOp: Pixels on backdrop, mosaics
    - Endgame: Drone, hanging, parking
    """
    # Auto components
    breakdown["comp_1"] = data.get("autoBackstageLeft", 0) + data.get("autoBackstageRight", 0)
    breakdown["comp_2"] = data.get("autoBackdropLeft", 0) + data.get("autoBackdropRight", 0)
    breakdown["comp_3"] = data.get("purplePixel1", False)
    breakdown["comp_4"] = data.get("purplePixel2", False)
    breakdown["comp_5"] = data.get("yellowPixel1", False)
    breakdown["comp_6"] = data.get("yellowPixel2", False)
    
    # TeleOp components
    breakdown["comp_7"] = data.get("dcBackstage", 0)
    breakdown["comp_8"] = data.get("dcBackdrop", 0)
    breakdown["comp_9"] = data.get("mosaics", 0)
    breakdown["comp_10"] = data.get("setLine", 0)
    
    # Endgame
    breakdown["comp_11"] = data.get("drone1", 0)
    breakdown["comp_12"] = data.get("drone2", 0)
    breakdown["comp_13"] = data.get("endgameParking1", 0)
    breakdown["comp_14"] = data.get("endgameParking2", 0)
    
    return breakdown


def parse_powerplay(breakdown: BreakdownDict, data: Dict[str, Any]) -> BreakdownDict:
    """
    Parse POWERPLAY (2022-2023) scoring breakdown
    
    Scoring elements:
    - Autonomous: Cones on junctions, terminal, signal
    - TeleOp: Cones on junctions
    - Endgame: Circuit, beacon
    """
    # Auto components
    breakdown["comp_1"] = data.get("autoTerminal", 0)
    breakdown["comp_2"] = data.get("autoJunctionCones", [])
    breakdown["comp_3"] = data.get("autoNavigated1", False)
    breakdown["comp_4"] = data.get("autoNavigated2", False)
    
    # TeleOp components
    breakdown["comp_5"] = data.get("dcTerminalNear", 0)
    breakdown["comp_6"] = data.get("dcTerminalFar", 0)
    breakdown["comp_7"] = data.get("dcJunctionCones", [])
    
    # Endgame
    breakdown["comp_8"] = data.get("egNavigated1", 0)
    breakdown["comp_9"] = data.get("egNavigated2", 0)
    breakdown["comp_10"] = data.get("coneOwnedJunctions", 0)
    breakdown["comp_11"] = data.get("beaconOwnedJunctions", 0)
    breakdown["comp_12"] = data.get("circuit", False)
    
    return breakdown


def parse_freight_frenzy(breakdown: BreakdownDict, data: Dict[str, Any]) -> BreakdownDict:
    """
    Parse FREIGHT FRENZY (2021-2022) scoring breakdown
    
    Scoring elements:
    - Autonomous: Carousel, duck delivery, warehouse parking
    - TeleOp: Freight in shipping hub, shared hub
    - Endgame: Capping, parking
    """
    # Auto
    breakdown["comp_1"] = data.get("autoCarousel", False)
    breakdown["comp_2"] = data.get("autoStorageFreight", 0)
    breakdown["comp_3"] = data.get("autoFreight1", 0)
    breakdown["comp_4"] = data.get("autoFreight2", 0)
    breakdown["comp_5"] = data.get("autoFreight3", 0)
    breakdown["comp_6"] = data.get("autoParked1", 0)
    breakdown["comp_7"] = data.get("autoParked2", 0)
    
    # TeleOp
    breakdown["comp_8"] = data.get("dcStorageFreight", 0)
    breakdown["comp_9"] = data.get("dcFreight1", 0)
    breakdown["comp_10"] = data.get("dcFreight2", 0)
    breakdown["comp_11"] = data.get("dcFreight3", 0)
    breakdown["comp_12"] = data.get("sharedFreight", 0)
    
    # Endgame
    breakdown["comp_13"] = data.get("endgameDelivered", 0)
    breakdown["comp_14"] = data.get("capped", 0)
    breakdown["comp_15"] = data.get("endgameParked1", 0)
    
    return breakdown


def parse_ultimate_goal(breakdown: BreakdownDict, data: Dict[str, Any]) -> BreakdownDict:
    """
    Parse ULTIMATE GOAL (2020-2021) scoring breakdown
    
    Scoring elements:
    - Autonomous: Wobble goals, power shots, rings in goal
    - TeleOp: Rings in goals
    - Endgame: Wobble goals, power shots
    """
    # Auto
    breakdown["comp_1"] = data.get("autoWobbleDelivered1", 0)
    breakdown["comp_2"] = data.get("autoWobbleDelivered2", 0)
    breakdown["comp_3"] = data.get("autoPowerShots", 0)
    breakdown["comp_4"] = data.get("autoTowerLow", 0)
    breakdown["comp_5"] = data.get("autoTowerMid", 0)
    breakdown["comp_6"] = data.get("autoTowerHigh", 0)
    breakdown["comp_7"] = data.get("autoNavigated1", False)
    breakdown["comp_8"] = data.get("autoNavigated2", False)
    
    # TeleOp
    breakdown["comp_9"] = data.get("dcTowerLow", 0)
    breakdown["comp_10"] = data.get("dcTowerMid", 0)
    breakdown["comp_11"] = data.get("dcTowerHigh", 0)
    
    # Endgame
    breakdown["comp_12"] = data.get("endgameWobbleGoal1", 0)
    breakdown["comp_13"] = data.get("endgameWobbleGoal2", 0)
    breakdown["comp_14"] = data.get("endgameWobbleRings1", 0)
    breakdown["comp_15"] = data.get("endgamePowerShots", 0)
    
    return breakdown


def parse_skystone(breakdown: BreakdownDict, data: Dict[str, Any]) -> BreakdownDict:
    """
    Parse SKYSTONE (2019-2020) scoring breakdown
    
    Scoring elements:
    - Autonomous: Skystones, stones delivered, foundation moved
    - TeleOp: Stones on foundation, skyscraper height
    - Endgame: Foundation moved, parking, capstone
    """
    # Auto
    breakdown["comp_1"] = data.get("autoDelivered", 0)
    breakdown["comp_2"] = data.get("autoSkystones", 0)
    breakdown["comp_3"] = data.get("autoPlaced", 0)
    breakdown["comp_4"] = data.get("autoReturned", 0)
    breakdown["comp_5"] = data.get("firstReturnedIsSkystone", False)
    breakdown["comp_6"] = data.get("autoRepositioned", False)
    breakdown["comp_7"] = data.get("autoNavigated1", False)
    breakdown["comp_8"] = data.get("autoNavigated2", False)
    
    # TeleOp
    breakdown["comp_9"] = data.get("dcDelivered", 0)
    breakdown["comp_10"] = data.get("dcPlaced", 0)
    breakdown["comp_11"] = data.get("dcReturned", 0)
    breakdown["comp_12"] = data.get("tallestSkyscraper", 0)
    
    # Endgame
    breakdown["comp_13"] = data.get("egFoundationMoved", False)
    breakdown["comp_14"] = data.get("egParked1", 0)
    breakdown["comp_15"] = data.get("capstone1", 0)
    
    return breakdown


# Mapping of component fields to human-readable names for each season
COMPONENT_NAMES = {
    2024: {
        "comp_1": "Auto Net Samples",
        "comp_2": "Auto Low Basket",
        "comp_3": "Auto High Basket",
        "comp_4": "Auto Low Chamber",
        "comp_5": "Auto High Chamber",
        "comp_6": "TeleOp Net Samples",
        "comp_7": "TeleOp Low Basket",
        "comp_8": "TeleOp High Basket",
        "comp_9": "TeleOp Low Chamber",
        "comp_10": "TeleOp High Chamber",
        "comp_11": "Robot 1 Ascent",
        "comp_12": "Robot 2 Ascent",
        "comp_13": "Robot 1 Auto Park",
        "comp_14": "Robot 2 Auto Park",
    },
    2023: {
        "comp_1": "Auto Backstage Pixels",
        "comp_2": "Auto Backdrop Pixels",
        "comp_3": "Purple Pixel 1",
        "comp_4": "Purple Pixel 2",
        "comp_5": "Yellow Pixel 1",
        "comp_6": "Yellow Pixel 2",
        "comp_7": "TeleOp Backstage",
        "comp_8": "TeleOp Backdrop",
        "comp_9": "Mosaics",
        "comp_10": "Set Lines",
        "comp_11": "Drone 1",
        "comp_12": "Drone 2",
        "comp_13": "Endgame Park 1",
        "comp_14": "Endgame Park 2",
    },
    2022: {
        "comp_1": "Auto Terminal",
        "comp_2": "Auto Junction Cones",
        "comp_3": "Auto Navigated 1",
        "comp_4": "Auto Navigated 2",
        "comp_5": "DC Terminal Near",
        "comp_6": "DC Terminal Far",
        "comp_7": "DC Junction Cones",
        "comp_8": "Endgame Navigated 1",
        "comp_9": "Endgame Navigated 2",
        "comp_10": "Owned Junctions",
        "comp_11": "Beacon Junctions",
        "comp_12": "Circuit",
    },
}
