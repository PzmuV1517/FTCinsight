"""
FTC Type Definitions

TypedDicts and types for FTC data structures.
"""

from typing import Dict, List, Optional, TypedDict, Any

from src.types.enums import CompLevel, MatchStatus, MatchWinner


class BreakdownDict(TypedDict, total=False):
    """FTC score breakdown dictionary"""
    total_points: int
    no_foul_points: int
    foul_points: int
    auto_points: int
    teleop_points: int
    endgame_points: int
    # Components - varies by year
    comp_1: float
    comp_2: float
    comp_3: float
    comp_4: float
    comp_5: float
    comp_6: float
    comp_7: float
    comp_8: float
    comp_9: float
    comp_10: float
    comp_11: float
    comp_12: float
    comp_13: float
    comp_14: float
    comp_15: float
    comp_16: float
    comp_17: float
    comp_18: float
    # Tiebreaker for playoffs
    tiebreaker: int
    # Ranking points (not used in FTC, kept for compatibility)
    rp_1: float
    rp_2: float
    rp_3: float


class TeamDict(TypedDict):
    """FTC team dictionary"""
    team: int
    name: str
    city: Optional[str]
    state: Optional[str]
    country: Optional[str]
    rookie_year: Optional[int]
    school_name: Optional[str]


class EventDict(TypedDict, total=False):
    """FTC event dictionary"""
    key: str
    name: str
    year: int
    week: int
    start_date: str
    end_date: str
    city: Optional[str]
    state: Optional[str]
    country: Optional[str]
    event_type: int
    district: Optional[str]


class MatchDict(TypedDict):
    """FTC match dictionary - all fields required for match creation"""
    key: str
    event: str
    year: int
    comp_level: CompLevel
    set_number: int
    match_number: int
    time: int
    predicted_time: int
    status: MatchStatus
    video: Optional[str]
    # Red alliance
    red_1: int
    red_2: int
    red_3: Optional[int]  # FTC typically has 2 teams per alliance
    red_dq: str
    red_surrogate: str
    red_score: int
    red_score_breakdown: BreakdownDict
    # Blue alliance
    blue_1: int
    blue_2: int
    blue_3: Optional[int]
    blue_dq: str
    blue_surrogate: str
    blue_score: int
    blue_score_breakdown: BreakdownDict
    # Result
    winner: MatchWinner


def empty_breakdown() -> BreakdownDict:
    """Return an empty breakdown dictionary with default values"""
    return BreakdownDict(
        total_points=0,
        no_foul_points=0,
        foul_points=0,
        auto_points=0,
        teleop_points=0,
        endgame_points=0,
        comp_1=0,
        comp_2=0,
        comp_3=0,
        comp_4=0,
        comp_5=0,
        comp_6=0,
        comp_7=0,
        comp_8=0,
        comp_9=0,
        comp_10=0,
        tiebreaker=0,
        rp_1=0,
        rp_2=0,
        rp_3=0,
    )
