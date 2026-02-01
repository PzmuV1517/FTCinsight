"""
SQL Storage Operations - ORM Based with Bulk Insert

Read/write operations for storing FTC Insight data in SQLite/PostgreSQL.
Uses SQLAlchemy ORM models with bulk insert for performance.
"""

from typing import Any, Dict, List, Optional
from sqlalchemy import inspect
from sqlalchemy.dialects.sqlite import insert

from src.db.main import Session, engine, init_db_from_models as _init_db_from_models, clean_db as _clean_db


def init_db():
    """Initialize the database, creating all tables from ORM models"""
    _init_db_from_models()
    print("Database initialized with ORM models")


def reset_db():
    """Drop and recreate all tables using ORM models"""
    _clean_db()
    print("Database reset successfully")


def _get_column_info(orm_class) -> dict:
    """Get column info including defaults and types for an ORM model"""
    mapper = inspect(orm_class)
    info = {}
    for column in mapper.columns:
        col_info = {
            "nullable": column.nullable,
            "default": None,
            "type": str(column.type),
        }
        
        if column.default is not None:
            col_info["default"] = column.default.arg if hasattr(column.default, 'arg') else column.default
        elif column.nullable:
            col_info["default"] = None
        else:
            # Provide sensible defaults for non-nullable fields without defaults
            type_str = str(column.type).upper()
            if "INT" in type_str:
                col_info["default"] = 0
            elif "FLOAT" in type_str or "REAL" in type_str:
                col_info["default"] = 0.0
            elif "BOOL" in type_str:
                col_info["default"] = False
            elif "VARCHAR" in type_str or "STRING" in type_str or "TEXT" in type_str:
                col_info["default"] = ""
            else:
                col_info["default"] = None
                
        info[column.key] = col_info
    return info


def _prepare_record(orm_class, data: Dict[str, Any]) -> Dict[str, Any]:
    """Prepare a record dict with defaults for bulk insert"""
    col_info = _get_column_info(orm_class)
    record = {}
    for col_name, info in col_info.items():
        if col_name in data and data[col_name] is not None:
            record[col_name] = data[col_name]
        elif info["default"] is not None or info["nullable"]:
            record[col_name] = info["default"]
    return record


def _bulk_upsert(orm_class, records: List[Dict[str, Any]], key_columns: List[str]) -> int:
    """Bulk upsert records using SQLite's INSERT OR REPLACE"""
    if not records:
        return 0
    
    session = Session()
    try:
        for record in records:
            stmt = insert(orm_class).values(**record)
            update_dict = {k: v for k, v in record.items() if k not in key_columns}
            if update_dict:
                stmt = stmt.on_conflict_do_update(
                    index_elements=key_columns,
                    set_=update_dict
                )
            session.execute(stmt)
        
        session.commit()
        return len(records)
    except Exception as e:
        session.rollback()
        print(f"Error in bulk upsert: {e}")
        raise
    finally:
        session.close()


# ============================================
# Team operations
# ============================================

def write_teams(teams: List[Dict[str, Any]]) -> int:
    """Write team data to database"""
    if not teams:
        return 0
    
    from src.db.models.team import TeamORM
    records = [_prepare_record(TeamORM, t) for t in teams]
    return _bulk_upsert(TeamORM, records, ['team'])


def read_teams(year: Optional[int] = None) -> List[Dict[str, Any]]:
    """Read all teams"""
    from src.db.models.team import TeamORM
    
    session = Session()
    try:
        teams = session.query(TeamORM).all()
        return [dict_from_orm(t) for t in teams]
    finally:
        session.close()


# ============================================
# Team Year operations
# ============================================

def write_team_years(team_years: List[Dict[str, Any]]) -> int:
    """Write team year data to database"""
    if not team_years:
        return 0
    
    from src.db.models.team_year import TeamYearORM
    records = [_prepare_record(TeamYearORM, ty) for ty in team_years]
    return _bulk_upsert(TeamYearORM, records, ['team', 'year'])


def read_team_years(year: int) -> List[Dict[str, Any]]:
    """Read team years for a specific year"""
    from src.db.models.team_year import TeamYearORM
    
    session = Session()
    try:
        team_years = session.query(TeamYearORM).filter(TeamYearORM.year == year).all()
        return [dict_from_orm(ty) for ty in team_years]
    finally:
        session.close()


# ============================================
# Event operations
# ============================================

def write_events(events: List[Dict[str, Any]]) -> int:
    """Write event data to database"""
    if not events:
        return 0
    
    from src.db.models.event import EventORM
    from src.types.enums import EventStatus, FTCEventType
    
    # Convert enums
    for event_data in events:
        status = event_data.get("status", "Upcoming")
        if isinstance(status, str):
            try:
                event_data["status"] = EventStatus(status)
            except ValueError:
                event_data["status"] = EventStatus.UPCOMING
        
        event_type = event_data.get("type", "Regional")
        if isinstance(event_type, str):
            try:
                event_data["type"] = FTCEventType(event_type)
            except ValueError:
                event_data["type"] = FTCEventType.QUALIFIER
    
    records = [_prepare_record(EventORM, e) for e in events]
    return _bulk_upsert(EventORM, records, ['key'])


def read_events(year: int) -> List[Dict[str, Any]]:
    """Read events for a specific year"""
    from src.db.models.event import EventORM
    
    session = Session()
    try:
        events = session.query(EventORM).filter(EventORM.year == year).all()
        return [dict_from_orm(e) for e in events]
    finally:
        session.close()


def read_event(event_key: str) -> Optional[Dict[str, Any]]:
    """Read a single event"""
    from src.db.models.event import EventORM
    
    session = Session()
    try:
        event = session.query(EventORM).filter(EventORM.key == event_key).first()
        return dict_from_orm(event) if event else None
    finally:
        session.close()


# ============================================
# Match operations
# ============================================

def write_matches(matches: List[Dict[str, Any]]) -> int:
    """Write match data to database"""
    if not matches:
        return 0
    
    from src.db.models.match import MatchORM
    from src.types.enums import CompLevel, MatchStatus, MatchWinner
    
    # Convert enums
    for match_data in matches:
        comp_level = match_data.get("comp_level", "qm")
        if isinstance(comp_level, str):
            try:
                match_data["comp_level"] = CompLevel(comp_level)
            except ValueError:
                match_data["comp_level"] = CompLevel.QUAL
        
        status = match_data.get("status", "Upcoming")
        if isinstance(status, str):
            try:
                match_data["status"] = MatchStatus(status)
            except ValueError:
                match_data["status"] = MatchStatus.UPCOMING
        
        winner = match_data.get("winner")
        if isinstance(winner, str) and winner:
            try:
                match_data["winner"] = MatchWinner(winner)
            except ValueError:
                match_data["winner"] = None
    
    records = [_prepare_record(MatchORM, m) for m in matches]
    return _bulk_upsert(MatchORM, records, ['key'])


def read_matches(event_key: str) -> List[Dict[str, Any]]:
    """Read matches for an event"""
    from src.db.models.match import MatchORM
    
    session = Session()
    try:
        matches = session.query(MatchORM).filter(MatchORM.event == event_key).all()
        return [dict_from_orm(m) for m in matches]
    finally:
        session.close()


# ============================================
# Team Event operations
# ============================================

def write_team_events(team_events: List[Dict[str, Any]]) -> int:
    """Write team-event data to database"""
    if not team_events:
        return 0
    
    from src.db.models.team_event import TeamEventORM
    from src.types.enums import EventStatus, FTCEventType
    
    # Ensure type and status have valid default values
    for te in team_events:
        te_type = te.get("type", "other")
        if not te_type or te_type == "":
            te["type"] = FTCEventType.OTHER
        elif isinstance(te_type, str):
            try:
                te["type"] = FTCEventType(te_type)
            except ValueError:
                te["type"] = FTCEventType.OTHER
        
        te_status = te.get("status", "Completed")
        if not te_status or te_status == "":
            te["status"] = EventStatus.COMPLETED
        elif isinstance(te_status, str):
            try:
                te["status"] = EventStatus(te_status)
            except ValueError:
                te["status"] = EventStatus.COMPLETED
    
    records = [_prepare_record(TeamEventORM, te) for te in team_events]
    return _bulk_upsert(TeamEventORM, records, ['team', 'event'])


# ============================================
# Team Match operations
# ============================================

def write_team_matches(team_matches: List[Dict[str, Any]]) -> int:
    """Write team-match data to database"""
    if not team_matches:
        return 0
    
    from src.db.models.team_match import TeamMatchORM
    records = [_prepare_record(TeamMatchORM, tm) for tm in team_matches]
    return _bulk_upsert(TeamMatchORM, records, ['team', 'match'])


# ============================================
# Year operations
# ============================================

def write_year(year_data: Dict[str, Any]) -> bool:
    """Write year statistics to database"""
    from src.db.models.year import YearORM
    
    records = [_prepare_record(YearORM, year_data)]
    _bulk_upsert(YearORM, records, ['year'])
    return True


def read_year(year: int) -> Optional[Dict[str, Any]]:
    """Read year statistics"""
    from src.db.models.year import YearORM
    
    session = Session()
    try:
        year_data = session.query(YearORM).filter(YearORM.year == year).first()
        return dict_from_orm(year_data) if year_data else None
    finally:
        session.close()


# ============================================
# Rankings operations
# ============================================

def write_rankings(event_key: str, rankings: List[Dict[str, Any]]) -> int:
    """Write event rankings - not implemented"""
    return 0


# ============================================
# Helper functions
# ============================================

def dict_from_orm(orm_instance) -> Dict[str, Any]:
    """Convert an ORM instance to a dictionary"""
    if orm_instance is None:
        return {}
    mapper = inspect(type(orm_instance))
    return {column.key: getattr(orm_instance, column.key) for column in mapper.columns}


# ============================================
# Metadata (in-memory for compatibility)
# ============================================

_metadata_store: Dict[str, Dict[str, Any]] = {}


def write_metadata(key: str, data: Dict[str, Any]) -> bool:
    """Write metadata to in-memory store"""
    _metadata_store[key] = data
    return True


def read_metadata(key: str) -> Optional[Dict[str, Any]]:
    """Read metadata from in-memory store"""
    return _metadata_store.get(key)
