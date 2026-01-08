from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, MappedAsDataclass, sessionmaker

from src.constants import CONN_STR, PROD

engine = create_engine(CONN_STR)

Session = sessionmaker(bind=engine)


# Only for type hints, doesn't enable slots
# Mirror to avoid intermediate commits to DB
class Base(MappedAsDataclass, DeclarativeBase):
    pass


def init_db_from_models() -> None:
    """Initialize database tables from SQLAlchemy ORM models"""
    # Import all models to register them with Base
    from src.db.models import team, team_year, event, match, team_event, team_match, year
    Base.metadata.create_all(bind=engine)
    print("Database tables created from ORM models")


def clean_db() -> None:
    # Import all models to register them with Base
    from src.db.models import team, team_year, event, match, team_event, team_match, year
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(engine)


def run_transaction(session_factory, callback):
    """
    Run a database transaction - works for both SQLite and CockroachDB.
    For SQLite, we just run the callback directly.
    For CockroachDB, we use the cockroachdb driver's run_transaction.
    """
    if PROD:
        # Use CockroachDB's run_transaction for production
        from sqlalchemy_cockroachdb import run_transaction as crdb_run_transaction
        return crdb_run_transaction(session_factory, callback)
    else:
        # For SQLite, just run the callback in a session
        session = session_factory()
        try:
            result = callback(session)
            session.commit()
            return result
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()
