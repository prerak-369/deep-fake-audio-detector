"""
SQLite database connection for VoiceGuard compliance case storage.
Uses SQLAlchemy sync engine — simple and sufficient for single-process hackathon use.
"""

import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, DeclarativeBase

os.makedirs("./memory_store", exist_ok=True)

DATABASE_URL = os.getenv("VOICEGUARD_DB_URL", "sqlite:///./memory_store/compliance.db")

engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False},
    echo=False,
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


class Base(DeclarativeBase):
    pass


def get_db():
    """FastAPI dependency — yields a DB session and closes it after the request."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
