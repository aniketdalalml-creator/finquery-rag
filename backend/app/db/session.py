"""Engine and session management.

The commit boundary is the request: `get_db` commits on success and rolls
back on any exception, so services/repositories never call commit() themselves
and every request is atomic.
"""

from __future__ import annotations

from collections.abc import Generator

from sqlalchemy import create_engine, event
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session, sessionmaker

from app.core.config import config


def _engine_kwargs(url: str) -> dict:
    if url.startswith("sqlite"):
        return {"connect_args": {"check_same_thread": False}}
    return {"pool_pre_ping": True, "pool_size": 5, "max_overflow": 10}


def register_sqlite_pragmas(target_engine: Engine) -> None:
    """Enforce FK constraints on SQLite (off by default, ON in PostgreSQL)."""
    if not target_engine.url.get_backend_name() == "sqlite":
        return

    @event.listens_for(target_engine, "connect")
    def _set_sqlite_pragma(dbapi_connection, _connection_record):
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()


engine = create_engine(config.DATABASE_URL, **_engine_kwargs(config.DATABASE_URL))
register_sqlite_pragmas(engine)

SessionLocal = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)


def get_db() -> Generator[Session, None, None]:
    """FastAPI dependency: one session per request, committed atomically."""
    db = SessionLocal()
    try:
        yield db
        db.commit()
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()
