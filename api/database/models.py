"""
ORM models for VoiceGuard compliance case storage.
Table is created automatically on import via Base.metadata.create_all().
"""

from sqlalchemy import Column, String, Float, Boolean, Text
from api.database.connection import Base, engine


class AudioCase(Base):
    """Episodic memory record — one row per submitted audio file."""

    __tablename__ = "audio_cases"

    case_id      = Column(String, primary_key=True, index=True)
    audio_path   = Column(String, nullable=True)
    filename     = Column(String, nullable=True)
    is_fake      = Column(Boolean, default=False)
    confidence   = Column(Float, default=0.0)
    proba_cnn    = Column(Float, nullable=True)
    proba_lstm   = Column(Float, nullable=True)
    proba_bio    = Column(Float, nullable=True)
    department   = Column(String, nullable=True, index=True)
    submitter    = Column(String, nullable=True)
    purpose      = Column(Text, nullable=True)
    timestamp    = Column(String, index=True)          # ISO-8601 UTC string
    analysis_text = Column(Text, nullable=True)
    report_path  = Column(String, nullable=True)
    risk_level   = Column(String, nullable=True)       # LOW/MEDIUM/HIGH/CRITICAL
    risk_score   = Column(Float, nullable=True)


# Auto-create table on first import
Base.metadata.create_all(bind=engine)
