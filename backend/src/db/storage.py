"""
SQL Storage Operations

Read/write operations for storing FTC Insight data in SQLite/PostgreSQL.
This replaces the Firebase Firestore storage for local development.
"""

from typing import Any, Dict, List, Optional
from datetime import datetime
from contextlib import contextmanager

from sqlalchemy import text, inspect
from sqlalchemy.dialects.sqlite import insert as sqlite_insert
from sqlalchemy.orm import Session as SessionType

from src.db.main import Session, engine, Base


@contextmanager
def get_session():
    """Get a database session with automatic commit/rollback"""
    session = Session()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


def init_db():
    """Initialize the database, creating all tables"""
    # Import all models to ensure they're registered with Base
    from src.db.models import team, team_year, event, match, team_event, team_match, year
    
    Base.metadata.create_all(engine)
    print("Database initialized successfully")


def reset_db():
    """Drop and recreate all tables"""
    # Import all models to ensure they're registered with Base
    from src.db.models import team, team_year, event, match, team_event, team_match, year
    
    Base.metadata.drop_all(engine)
    Base.metadata.create_all(engine)
    print("Database reset successfully")


def get_model_columns(orm_class) -> set:
    """Get the column names for an ORM model"""
    mapper = inspect(orm_class)
    return {column.key for column in mapper.columns}


def filter_dict_for_model(data: Dict[str, Any], orm_class) -> Dict[str, Any]:
    """Filter a dictionary to only include keys that are columns in the ORM model"""
    valid_columns = get_model_columns(orm_class)
    return {k: v for k, v in data.items() if k in valid_columns}


def batch_upsert(table_name: str, documents: List[Dict[str, Any]], key_columns: List[str]) -> int:
    """
    Batch upsert documents to a SQL table using INSERT OR REPLACE for SQLite
    
    Args:
        table_name: Name of the table
        documents: List of document dictionaries
        key_columns: Primary key column(s) for conflict resolution
    
    Returns:
        Number of documents written
    """
    if not documents:
        return 0
    
    # Add timestamp to all documents
    for doc in documents:
        doc["_updated_at"] = datetime.utcnow().isoformat()
    
    with get_session() as session:
        # Use raw SQL for bulk insert with conflict handling
        # SQLite uses INSERT OR REPLACE, PostgreSQL uses ON CONFLICT
        table = Base.metadata.tables.get(table_name)
        if table is None:
            raise ValueError(f"Table {table_name} not found")
        
        # Batch insert in chunks
        batch_size = 500
        total_written = 0
        
        for i in range(0, len(documents), batch_size):
            chunk = documents[i:i + batch_size]
            
            # Use SQLite's INSERT OR REPLACE
            stmt = sqlite_insert(table).values(chunk)
            stmt = stmt.on_conflict_do_update(
                index_elements=key_columns,
                set_={col: stmt.excluded[col] for col in chunk[0].keys() if col not in key_columns}
            )
            
            session.execute(stmt)
            total_written += len(chunk)
        
        session.commit()
    
    return total_written


def simple_batch_insert(table_name: str, documents: List[Dict[str, Any]]) -> int:
    """
    Simple batch insert (replaces existing data)
    Deletes existing records with same keys and inserts new ones.
    
    Args:
        table_name: Name of the table
        documents: List of document dictionaries
    
    Returns:
        Number of documents written
    """
    if not documents:
        return 0
    
    with get_session() as session:
        table = Base.metadata.tables.get(table_name)
        if table is None:
            raise ValueError(f"Table {table_name} not found")
        
        # Batch insert in chunks
        batch_size = 500
        total_written = 0
        
        for i in range(0, len(documents), batch_size):
            chunk = documents[i:i + batch_size]
            session.execute(table.insert(), chunk)
            total_written += len(chunk)
        
        session.commit()
    
    return total_written


# ============================================
# Team operations
# ============================================

def write_teams(teams: List[Dict[str, Any]]) -> int:
    """Write team data to database"""
    if not teams:
        return 0
    
    with get_session() as session:
        from src.db.models.team import TeamORM
        
        for team_data in teams:
            team_num = team_data.get("team")
            existing = session.query(TeamORM).filter(TeamORM.team == team_num).first()
            
            if existing:
                for key, value in team_data.items():
                    if hasattr(existing, key) and key != "team":
                        setattr(existing, key, value)
            else:
                # Create new team with required fields
                new_team = TeamORM(
                    team=team_data["team"],
                    name=team_data.get("name", f"Team {team_data['team']}"),
                    country=team_data.get("country"),
                    state=team_data.get("state"),
                    rookie_year=team_data.get("rookie_year"),
                    district=team_data.get("district"),
                    active=team_data.get("active", False),
                    wins=team_data.get("wins", 0),
                    losses=team_data.get("losses", 0),
                    ties=team_data.get("ties", 0),
                    count=team_data.get("count", 0),
                    winrate=team_data.get("winrate", 0.0),
                    norm_epa=team_data.get("norm_epa"),
                    norm_epa_recent=team_data.get("norm_epa_recent"),
                    norm_epa_mean=team_data.get("norm_epa_mean"),
                    norm_epa_max=team_data.get("norm_epa_max"),
                )
                session.add(new_team)
        
        session.commit()
    
    return len(teams)


def read_teams(year: Optional[int] = None) -> List[Dict[str, Any]]:
    """Read all teams, optionally filtered by active status"""
    with get_session() as session:
        from src.db.models.team import TeamORM
        
        query = session.query(TeamORM)
        if year:
            query = query.filter(TeamORM.active == True)
        
        teams = query.all()
        return [
            {
                "team": t.team,
                "name": t.name,
                "country": t.country,
                "state": t.state,
                "rookie_year": t.rookie_year,
                "district": t.district,
                "active": t.active,
                "wins": t.wins,
                "losses": t.losses,
                "ties": t.ties,
                "count": t.count,
                "winrate": t.winrate,
                "norm_epa": t.norm_epa,
                "norm_epa_recent": t.norm_epa_recent,
                "norm_epa_mean": t.norm_epa_mean,
                "norm_epa_max": t.norm_epa_max,
            }
            for t in teams
        ]


# ============================================
# Team Year operations
# ============================================

def write_team_years(team_years: List[Dict[str, Any]]) -> int:
    """Write team year data to database"""
    if not team_years:
        return 0
    
    with get_session() as session:
        from src.db.models.team_year import TeamYearORM
        
        for ty_data in team_years:
            team = ty_data.get("team")
            year = ty_data.get("year")
            
            existing = session.query(TeamYearORM).filter(
                TeamYearORM.team == team,
                TeamYearORM.year == year
            ).first()
            
            if existing:
                for key, value in ty_data.items():
                    if hasattr(existing, key) and key not in ("team", "year"):
                        setattr(existing, key, value)
            else:
                new_ty = TeamYearORM(
                    team=team,
                    year=year,
                    name=ty_data.get("name", f"Team {team}"),
                    country=ty_data.get("country"),
                    state=ty_data.get("state"),
                    district=ty_data.get("district"),
                    is_competing=ty_data.get("is_competing", False),
                    next_event_key=ty_data.get("next_event_key"),
                    next_event_name=ty_data.get("next_event_name"),
                    next_event_week=ty_data.get("next_event_week"),
                    epa_start=ty_data.get("epa_start", 0.0),
                    epa_pre_champs=ty_data.get("epa_pre_champs"),
                    epa_end=ty_data.get("epa_end"),
                    epa_mean=ty_data.get("epa_mean"),
                    epa_max=ty_data.get("epa_max"),
                    epa_diff=ty_data.get("epa_diff"),
                    auto_epa_start=ty_data.get("auto_epa_start"),
                    auto_epa_pre_champs=ty_data.get("auto_epa_pre_champs"),
                    auto_epa_end=ty_data.get("auto_epa_end"),
                    auto_epa_mean=ty_data.get("auto_epa_mean"),
                    auto_epa_max=ty_data.get("auto_epa_max"),
                    teleop_epa_start=ty_data.get("teleop_epa_start"),
                    teleop_epa_pre_champs=ty_data.get("teleop_epa_pre_champs"),
                    teleop_epa_end=ty_data.get("teleop_epa_end"),
                    teleop_epa_mean=ty_data.get("teleop_epa_mean"),
                    teleop_epa_max=ty_data.get("teleop_epa_max"),
                    endgame_epa_start=ty_data.get("endgame_epa_start"),
                    endgame_epa_pre_champs=ty_data.get("endgame_epa_pre_champs"),
                    endgame_epa_end=ty_data.get("endgame_epa_end"),
                    endgame_epa_mean=ty_data.get("endgame_epa_mean"),
                    endgame_epa_max=ty_data.get("endgame_epa_max"),
                    epa_rank=ty_data.get("epa_rank"),
                    epa_count=ty_data.get("epa_count"),
                    epa_percentile=ty_data.get("epa_percentile"),
                    state_epa_rank=ty_data.get("state_epa_rank"),
                    state_epa_count=ty_data.get("state_epa_count"),
                    country_epa_rank=ty_data.get("country_epa_rank"),
                    country_epa_count=ty_data.get("country_epa_count"),
                    district_epa_rank=ty_data.get("district_epa_rank"),
                    district_epa_count=ty_data.get("district_epa_count"),
                    wins=ty_data.get("wins", 0),
                    losses=ty_data.get("losses", 0),
                    ties=ty_data.get("ties", 0),
                    count=ty_data.get("count", 0),
                    winrate=ty_data.get("winrate", 0.0),
                    qual_wins=ty_data.get("qual_wins", 0),
                    qual_losses=ty_data.get("qual_losses", 0),
                    qual_ties=ty_data.get("qual_ties", 0),
                    qual_count=ty_data.get("qual_count", 0),
                )
                session.add(new_ty)
        
        session.commit()
    
    return len(team_years)


def read_team_years(year: int) -> List[Dict[str, Any]]:
    """Read team years for a specific year"""
    with get_session() as session:
        from src.db.models.team_year import TeamYearORM
        
        team_years = session.query(TeamYearORM).filter(TeamYearORM.year == year).all()
        return [
            {
                "team": ty.team,
                "year": ty.year,
                "name": ty.name,
                "country": ty.country,
                "state": ty.state,
                "epa_end": ty.epa_end,
                "epa_rank": ty.epa_rank,
                "wins": ty.wins,
                "losses": ty.losses,
                "count": ty.count,
            }
            for ty in team_years
        ]


# ============================================
# Event operations
# ============================================

def write_events(events: List[Dict[str, Any]]) -> int:
    """Write event data to database"""
    if not events:
        return 0
    
    with get_session() as session:
        from src.db.models.event import EventORM
        
        for event_data in events:
            key = event_data.get("key")
            existing = session.query(EventORM).filter(EventORM.key == key).first()
            
            if existing:
                for k, value in event_data.items():
                    if hasattr(existing, k) and k != "key":
                        setattr(existing, k, value)
            else:
                new_event = EventORM(
                    key=key,
                    year=event_data.get("year"),
                    name=event_data.get("name", "Unknown Event"),
                    time=event_data.get("time", 0),
                    country=event_data.get("country"),
                    state=event_data.get("state"),
                    district=event_data.get("district"),
                    start_date=event_data.get("start_date", ""),
                    end_date=event_data.get("end_date", ""),
                    type=event_data.get("type", "Regional"),
                    week=event_data.get("week", 0),
                    video=event_data.get("video"),
                    status=event_data.get("status", "Upcoming"),
                    num_teams=event_data.get("num_teams", 0),
                    current_match=event_data.get("current_match"),
                    qual_matches=event_data.get("qual_matches"),
                    epa_max=event_data.get("epa_max"),
                    epa_top_8=event_data.get("epa_top_8"),
                    epa_top_24=event_data.get("epa_top_24"),
                    epa_mean=event_data.get("epa_mean"),
                    epa_sd=event_data.get("epa_sd"),
                    count=event_data.get("count", 0),
                )
                session.add(new_event)
        
        session.commit()
    
    return len(events)


def read_events(year: int) -> List[Dict[str, Any]]:
    """Read events for a specific year"""
    with get_session() as session:
        from src.db.models.event import EventORM
        
        events = session.query(EventORM).filter(EventORM.year == year).all()
        return [e.to_dict() for e in events]


def read_event(event_key: str) -> Optional[Dict[str, Any]]:
    """Read a single event"""
    with get_session() as session:
        from src.db.models.event import EventORM
        
        event = session.query(EventORM).filter(EventORM.key == event_key).first()
        return event.to_dict() if event else None


# ============================================
# Match operations
# ============================================

def write_matches(matches: List[Dict[str, Any]]) -> int:
    """Write match data to database"""
    if not matches:
        return 0
    
    with get_session() as session:
        from src.db.models.match import MatchORM
        
        for match_data in matches:
            key = match_data.get("key")
            existing = session.query(MatchORM).filter(MatchORM.key == key).first()
            
            if existing:
                for k, value in match_data.items():
                    if hasattr(existing, k) and k != "key":
                        setattr(existing, k, value)
            else:
                new_match = MatchORM(
                    key=key,
                    year=match_data.get("year"),
                    event=match_data.get("event"),
                    week=match_data.get("week", 0),
                    elim=match_data.get("elim", False),
                    comp_level=match_data.get("comp_level", "qm"),
                    set_number=match_data.get("set_number", 1),
                    match_number=match_data.get("match_number", 1),
                    time=match_data.get("time", 0),
                    predicted_time=match_data.get("predicted_time"),
                    status=match_data.get("status", "Upcoming"),
                    video=match_data.get("video"),
                    red_1=match_data.get("red_1", 0),
                    red_2=match_data.get("red_2", 0),
                    red_3=match_data.get("red_3"),
                    red_dq=match_data.get("red_dq", ""),
                    red_surrogate=match_data.get("red_surrogate", ""),
                    blue_1=match_data.get("blue_1", 0),
                    blue_2=match_data.get("blue_2", 0),
                    blue_3=match_data.get("blue_3"),
                    blue_dq=match_data.get("blue_dq", ""),
                    blue_surrogate=match_data.get("blue_surrogate", ""),
                    winner=match_data.get("winner"),
                    red_score=match_data.get("red_score"),
                    red_no_foul=match_data.get("red_no_foul"),
                    red_foul=match_data.get("red_foul"),
                    red_auto=match_data.get("red_auto"),
                    red_teleop=match_data.get("red_teleop"),
                    red_endgame=match_data.get("red_endgame"),
                    blue_score=match_data.get("blue_score"),
                    blue_no_foul=match_data.get("blue_no_foul"),
                    blue_foul=match_data.get("blue_foul"),
                    blue_auto=match_data.get("blue_auto"),
                    blue_teleop=match_data.get("blue_teleop"),
                    blue_endgame=match_data.get("blue_endgame"),
                )
                session.add(new_match)
        
        session.commit()
    
    return len(matches)


def read_matches(event_key: str) -> List[Dict[str, Any]]:
    """Read matches for an event"""
    with get_session() as session:
        from src.db.models.match import MatchORM
        
        matches = session.query(MatchORM).filter(MatchORM.event == event_key).all()
        return [m.to_dict() for m in matches]


# ============================================
# Team Event operations
# ============================================

def write_team_events(team_events: List[Dict[str, Any]]) -> int:
    """Write team-event data to database"""
    if not team_events:
        return 0
    
    with get_session() as session:
        from src.db.models.team_event import TeamEventORM
        
        for te_data in team_events:
            team = te_data.get("team")
            event = te_data.get("event")
            
            existing = session.query(TeamEventORM).filter(
                TeamEventORM.team == team,
                TeamEventORM.event == event
            ).first()
            
            if existing:
                for k, value in te_data.items():
                    if hasattr(existing, k) and k not in ("team", "event"):
                        setattr(existing, k, value)
            else:
                new_te = TeamEventORM(
                    team=team,
                    year=te_data.get("year"),
                    event=event,
                    week=te_data.get("week", 0),
                    time=te_data.get("time", 0),
                    first_event=te_data.get("first_event", False),
                    offseason=te_data.get("offseason", False),
                    rank=te_data.get("rank"),
                    num_teams=te_data.get("num_teams"),
                    epa_start=te_data.get("epa_start"),
                    epa_pre_elim=te_data.get("epa_pre_elim"),
                    epa_end=te_data.get("epa_end"),
                    epa_mean=te_data.get("epa_mean"),
                    epa_max=te_data.get("epa_max"),
                    epa_diff=te_data.get("epa_diff"),
                    wins=te_data.get("wins", 0),
                    losses=te_data.get("losses", 0),
                    ties=te_data.get("ties", 0),
                    count=te_data.get("count", 0),
                    winrate=te_data.get("winrate", 0.0),
                    qual_wins=te_data.get("qual_wins", 0),
                    qual_losses=te_data.get("qual_losses", 0),
                    qual_ties=te_data.get("qual_ties", 0),
                    qual_count=te_data.get("qual_count", 0),
                )
                session.add(new_te)
        
        session.commit()
    
    return len(team_events)


# ============================================
# Team Match operations
# ============================================

def write_team_matches(team_matches: List[Dict[str, Any]]) -> int:
    """Write team-match data to database"""
    if not team_matches:
        return 0
    
    with get_session() as session:
        from src.db.models.team_match import TeamMatchORM
        
        for tm_data in team_matches:
            team = tm_data.get("team")
            match = tm_data.get("match")
            
            existing = session.query(TeamMatchORM).filter(
                TeamMatchORM.team == team,
                TeamMatchORM.match == match
            ).first()
            
            if existing:
                for k, value in tm_data.items():
                    if hasattr(existing, k) and k not in ("team", "match"):
                        setattr(existing, k, value)
            else:
                new_tm = TeamMatchORM(
                    team=team,
                    year=tm_data.get("year"),
                    event=tm_data.get("event"),
                    match=match,
                    week=tm_data.get("week", 0),
                    time=tm_data.get("time", 0),
                    alliance=tm_data.get("alliance", "red"),
                    dq=tm_data.get("dq", False),
                    surrogate=tm_data.get("surrogate", False),
                    status=tm_data.get("status", "Upcoming"),
                    epa=tm_data.get("epa"),
                    auto_epa=tm_data.get("auto_epa"),
                    teleop_epa=tm_data.get("teleop_epa"),
                    endgame_epa=tm_data.get("endgame_epa"),
                    post_epa=tm_data.get("post_epa"),
                )
                session.add(new_tm)
        
        session.commit()
    
    return len(team_matches)


# ============================================
# Year operations
# ============================================

def write_year(year_data: Dict[str, Any]) -> bool:
    """Write year statistics to database"""
    with get_session() as session:
        from src.db.models.year import YearORM
        
        year = year_data.get("year")
        existing = session.query(YearORM).filter(YearORM.year == year).first()
        
        if existing:
            for k, value in year_data.items():
                if hasattr(existing, k) and k != "year":
                    setattr(existing, k, value)
        else:
            new_year = YearORM(
                year=year,
                epa_max=year_data.get("epa_max"),
                epa_1p=year_data.get("epa_1p"),
                epa_5p=year_data.get("epa_5p"),
                epa_10p=year_data.get("epa_10p"),
                epa_25p=year_data.get("epa_25p"),
                epa_median=year_data.get("epa_median"),
                epa_mean=year_data.get("epa_mean"),
                epa_sd=year_data.get("epa_sd"),
                auto_epa_max=year_data.get("auto_epa_max"),
                auto_epa_mean=year_data.get("auto_epa_mean"),
                auto_epa_sd=year_data.get("auto_epa_sd"),
                teleop_epa_max=year_data.get("teleop_epa_max"),
                teleop_epa_mean=year_data.get("teleop_epa_mean"),
                teleop_epa_sd=year_data.get("teleop_epa_sd"),
                endgame_epa_max=year_data.get("endgame_epa_max"),
                endgame_epa_mean=year_data.get("endgame_epa_mean"),
                endgame_epa_sd=year_data.get("endgame_epa_sd"),
                score_mean=year_data.get("score_mean"),
                score_sd=year_data.get("score_sd"),
                foul_mean=year_data.get("foul_mean"),
                no_foul_mean=year_data.get("no_foul_mean"),
                auto_mean=year_data.get("auto_mean"),
                teleop_mean=year_data.get("teleop_mean"),
                endgame_mean=year_data.get("endgame_mean"),
                count=year_data.get("count", 0),
            )
            session.add(new_year)
        
        session.commit()
    
    return True


def read_year(year: int) -> Optional[Dict[str, Any]]:
    """Read year statistics"""
    with get_session() as session:
        from src.db.models.year import YearORM
        
        year_data = session.query(YearORM).filter(YearORM.year == year).first()
        return year_data.to_dict() if year_data else None


# ============================================
# Rankings operations
# ============================================

def write_rankings(event_key: str, rankings: List[Dict[str, Any]]) -> int:
    """Write event rankings to database (stored as JSON in event)"""
    # For now, rankings can be stored in the event or in a separate table
    # This is a simplified version that stores in a separate rankings table
    return 0  # TODO: Implement if needed


# ============================================
# Metadata operations
# ============================================

_metadata_store: Dict[str, Dict[str, Any]] = {}

def write_metadata(key: str, data: Dict[str, Any]) -> bool:
    """Write metadata (last update times, etc.) - stored in memory for now"""
    _metadata_store[key] = data
    return True


def read_metadata(key: str) -> Optional[Dict[str, Any]]:
    """Read metadata"""
    return _metadata_store.get(key)
