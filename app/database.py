# File: app/database.py
# Purpose: SQLAlchemy engine, session factory, and Base for all models.
from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker

from app.core.config import settings

engine       = create_engine(settings.DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base         = declarative_base()


def get_db():
    """Yield a DB session and close it when done."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def get_engine(database_url: str = settings.DATABASE_URL):
    """Create a new SQLAlchemy engine for the given URL."""
    return create_engine(database_url)


def get_sessionmaker(eng):
    """Create a sessionmaker bound to the given engine."""
    return sessionmaker(autocommit=False, autoflush=False, bind=eng)
