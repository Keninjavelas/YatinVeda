"""Database session management for YatinVeda backend.

Provides SQLAlchemy engine, SessionLocal, and init_db/get_db helpers used
by the FastAPI application and tests.
"""

import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from models.database import Base


DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./yatinveda.db")

# SQLite needs check_same_thread=False for usage across threads (e.g. TestClient)
engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False} if DATABASE_URL.startswith("sqlite") else {},
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def init_db() -> None:
    """Initialize database schema for the default engine.

    In tests an in-memory engine is used instead; this function is mostly
    relevant for local development and will no-op if tables already exist.
    """
    Base.metadata.create_all(bind=engine)


def get_db():
    """FastAPI dependency that yields a database session."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
