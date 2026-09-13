"""
app/core/database.py
--------------------
SQLAlchemy database engine and session management.
Uses PostgreSQL via psycopg (v3). Configure DATABASE_URL in .env:
  DATABASE_URL=postgresql+psycopg://postgres:secret@localhost:5432/learnable
"""
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from .config import settings

engine = create_engine(
    settings.DATABASE_URL,
    echo=settings.DEBUG,        # Log SQL in debug mode
    pool_size=5,                # Maintained persistent connections
    max_overflow=10,            # Extra connections beyond pool_size
    pool_pre_ping=True,         # Verify connection is alive before using it
    connect_args={"prepare_threshold": None},  # Supabase transaction pooler compatibility
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()


def get_db():
    """Dependency: yields a DB session and closes it after the request."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def create_tables():
    """Create all tables defined in models. Called at app startup."""
    Base.metadata.create_all(bind=engine)
