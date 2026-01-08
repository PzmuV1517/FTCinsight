from typing import Optional, TypedDict, Union

try:
    from src.types.enums import CompLevel, FTCEventType, MatchStatus, MatchWinner
except ImportError:
    from ..types.enums import CompLevel, FTCEventType, MatchStatus, MatchWinner


class TeamDict(TypedDict):
    """FTC Team data structure"""
    team: int
    name: str
    rookie_year: Optional[int]
    country: Optional[str]
    state: Optional[str]
    city: Optional[str]
    school_name: Optional[str]
    website: Optional[str]
    region: Optional[str]


class EventDict(TypedDict):
    """FTC Event data structure"""
    year: int
    key: str  # format: {season}_{eventCode}
    event_code: str
    name: str
    country: Optional[str]
    state: Optional[str]
    city: Optional[str]
    venue: Optional[str]
    region: Optional[str]
    league_code: Optional[str]
    start_date: str
    end_date: str
    time: int
    type: FTCEventType
    week: int
    website: Optional[str]
    published: bool


class BreakdownDict(TypedDict):
    """FTC Match score breakdown - varies by game/season"""
    score: Optional[int]
    auto_points: Optional[int]
    teleop_points: Optional[int]
    endgame_points: Optional[int]
    penalty_points_committed: Optional[int]
    # Generic component fields - will be populated based on game
    comp_1: Optional[Union[int, float]]
    comp_2: Optional[Union[int, float]]
    comp_3: Optional[Union[int, float]]
    comp_4: Optional[Union[int, float]]
    comp_5: Optional[Union[int, float]]
    comp_6: Optional[Union[int, float]]
    comp_7: Optional[Union[int, float]]
    comp_8: Optional[Union[int, float]]
    comp_9: Optional[Union[int, float]]
    comp_10: Optional[Union[int, float]]
    comp_11: Optional[Union[int, float]]
    comp_12: Optional[Union[int, float]]
    comp_13: Optional[Union[int, float]]
    comp_14: Optional[Union[int, float]]
    comp_15: Optional[Union[int, float]]


empty_breakdown: BreakdownDict = {
    "score": 0,
    "auto_points": None,
    "teleop_points": None,
    "endgame_points": None,
    "penalty_points_committed": None,
    "comp_1": None,
    "comp_2": None,
    "comp_3": None,
    "comp_4": None,
    "comp_5": None,
    "comp_6": None,
    "comp_7": None,
    "comp_8": None,
    "comp_9": None,
    "comp_10": None,
    "comp_11": None,
    "comp_12": None,
    "comp_13": None,
    "comp_14": None,
    "comp_15": None,
}


class MatchDict(TypedDict):
    """FTC Match data structure"""
    event: str  # event key
    key: str  # match key: {event}_{comp_level}{match_number}
    comp_level: CompLevel
    series: int  # for playoff matches
    match_number: int
    status: MatchStatus
    # FTC has 2 teams per alliance
    red_1: int
    red_2: int
    red_surrogate_1: bool
    red_surrogate_2: bool
    blue_1: int
    blue_2: int
    blue_surrogate_1: bool
    blue_surrogate_2: bool
    winner: Optional[MatchWinner]
    time: Optional[int]  # scheduled time
    actual_time: Optional[int]
    post_result_time: Optional[int]
    red_score: Optional[int]
    blue_score: Optional[int]
    red_score_breakdown: BreakdownDict
    blue_score_breakdown: BreakdownDict


class RankingDict(TypedDict):
    """FTC Team ranking at an event"""
    team: int
    rank: int
    wins: int
    losses: int
    ties: int
    qual_average: Optional[float]
    ranking_points: Optional[float]
    tie_breaker_points: Optional[float]
    matches_played: int
    dq: int
    sort_order_1: Optional[float]
    sort_order_2: Optional[float]
    sort_order_3: Optional[float]
    sort_order_4: Optional[float]
    sort_order_5: Optional[float]
    sort_order_6: Optional[float]


class AllianceDict(TypedDict):
    """FTC Alliance selection data"""
    alliance_number: int
    captain: int
    pick_1: int
    pick_2: Optional[int]
    name: Optional[str]


class AwardDict(TypedDict):
    """FTC Award data"""
    award_id: int
    name: str
    team: Optional[int]
    person: Optional[str]
    event_code: str
    season: int
