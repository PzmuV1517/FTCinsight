from enum import Enum


class MatchWinner(str, Enum):
    RED = "red"
    BLUE = "blue"
    TIE = "tie"


class MatchStatus(str, Enum):
    UPCOMING = "Upcoming"
    COMPLETED = "Completed"


class CompLevel(str, Enum):
    INVALID = "invalid"
    QUAL = "qm"
    EIGHTH = "ef"
    QUARTER = "qf"
    SEMI = "sf"
    FINAL = "f"


class EventStatus(str, Enum):
    INVALID = "Invalid"
    UPCOMING = "Upcoming"
    ONGOING = "Ongoing"
    COMPLETED = "Completed"


# FRC Event Types (legacy)
class EventType(str, Enum):
    INVALID = "invalid"
    REGIONAL = "regional"
    DISTRICT = "district"
    DISTRICT_CMP = "district_cmp"
    CHAMPS_DIV = "champs_div"
    EINSTEIN = "einstein"
    # OFFSEASON = "offseason"

    def is_champs(self: "EventType") -> bool:
        return self in (EventType.CHAMPS_DIV, EventType.EINSTEIN)


# FTC Event Types
class FTCEventType(str, Enum):
    INVALID = "invalid"
    SCRIMMAGE = "scrimmage"
    LEAGUE_MEET = "league_meet"
    QUALIFIER = "qualifier"
    LEAGUE_TOURNAMENT = "league_tournament"
    CHAMPIONSHIP = "championship"
    SUPER_QUALIFIER = "super_qualifier"
    REGIONAL_CHAMPIONSHIP = "regional_championship"
    FIRST_CHAMPIONSHIP = "first_championship"
    OFFSEASON = "offseason"
    OTHER = "other"

    def is_champs(self: "FTCEventType") -> bool:
        return self in (FTCEventType.REGIONAL_CHAMPIONSHIP, FTCEventType.FIRST_CHAMPIONSHIP)

    def is_official(self: "FTCEventType") -> bool:
        return self not in (FTCEventType.SCRIMMAGE, FTCEventType.OFFSEASON, FTCEventType.OTHER, FTCEventType.INVALID)
