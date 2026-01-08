import uuid


def get_team_year_key(team: int, year: int) -> str:
    return str(team) + "_" + str(year)


def get_team_event_key(team: int, event: str) -> str:
    return str(team) + "_" + event


def get_team_match_key(team: int, match: str) -> str:
    return str(team) + "_" + match


def get_match_name(key: str) -> str:
    # Extract match portion from key (format: year_event_match or event_match)
    parts = key.split("_")
    if len(parts) >= 3:
        match_part = parts[-1]  # Last part is the match identifier
    elif len(parts) == 2:
        match_part = parts[1]
    else:
        match_part = key

    # FTC format: qm0m1, f0m1, sf0m1, etc.
    if match_part.startswith("qm"):
        # Qualifier match: qm0m1 -> Qual 1
        if "m" in match_part[2:]:
            match_num = match_part.split("m")[-1]
            return "Qual " + match_num
        return "Qual " + match_part[2:]
    elif match_part.startswith("sf"):
        # Semifinal: sf0m1 -> Semis 1 Match 1
        rest = match_part[2:]
        if "m" in rest:
            set_num = rest.split("m")[0]
            match_num = rest.split("m")[1]
            return "Semis " + set_num + " Match " + match_num
        return "Semis " + rest
    elif match_part.startswith("f"):
        # Finals: f0m1 -> Finals Match 1
        rest = match_part[1:]
        if "m" in rest:
            match_num = rest.split("m")[-1]
            return "Finals Match " + match_num
        return "Finals " + rest
    elif match_part.startswith("ef"):
        set_num = match_part.split("ef")[1].split("m")[0]
        match_num = match_part.split("ef")[1].split("m")[1]
        return "Eighths " + set_num + " Match " + match_num
    elif match_part.startswith("qf"):
        set_num = match_part.split("qf")[1].split("m")[0]
        match_num = match_part.split("qf")[1].split("m")[1]
        return "Quarters " + set_num + " Match " + match_num

    # Fallback: return the match part as-is rather than raising an error
    return match_part


def get_match_number(key: str) -> int:
    # Extract match portion from key
    parts = key.split("_")
    if len(parts) >= 3:
        match_part = parts[-1]
    elif len(parts) == 2:
        match_part = parts[1]
    else:
        match_part = key

    # FTC format: qm0m1, f0m1, sf0m1, etc.
    if match_part.startswith("qm"):
        if "m" in match_part[2:]:
            return int(match_part.split("m")[-1])
        return int(match_part[2:])
    elif match_part.startswith("qf"):
        rest = match_part[2:]
        if "m" in rest:
            set_num = rest.split("m")[0]
            match_num = rest.split("m")[1]
            return 100 + 10 * int(set_num) + int(match_num)
        return 100 + int(rest)
    elif match_part.startswith("sf"):
        rest = match_part[2:]
        if "m" in rest:
            set_num = rest.split("m")[0]
            match_num = rest.split("m")[1]
            return 200 + 10 * int(set_num) + int(match_num)
        return 200 + int(rest)
    elif match_part.startswith("f"):
        rest = match_part[1:]
        if "m" in rest:
            return 300 + int(rest.split("m")[-1])
        return 300 + int(rest)

    # Fallback: return 0
    return 0


def r(x: float, n: int = 0) -> float:
    return int(x * (10**n) + 0.5) / (10**n)


def is_uuid(s: str) -> bool:
    try:
        uuid.UUID(s)
        return True
    except ValueError:
        return False
