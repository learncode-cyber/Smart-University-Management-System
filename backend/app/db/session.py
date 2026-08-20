"""
SQLAlchemy engine + session factory.

`get_db()` is a FastAPI dependency (used from Part 2 onward) that yields
one session per request and always closes it, even on error — this is
what prevents connection-pool exhaustion under load.
"""
from collections.abc import Generator

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session

from app.core.config import settings

engine = create_engine(settings.DATABASE_URL, pool_pre_ping=True)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_db() -> Generator[Session, None, None]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
