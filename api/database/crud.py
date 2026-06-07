"""
CRUD operations for VoiceGuard compliance case storage.
All functions operate on a SQLAlchemy Session passed in by the caller.
"""

from datetime import datetime, timedelta, timezone
from sqlalchemy.orm import Session
from api.database.models import AudioCase


def _row_to_dict(row: AudioCase) -> dict:
    """Convert an ORM row to a plain dict, stripping SQLAlchemy internals."""
    return {
        "case_id":       row.case_id,
        "audio_path":    row.audio_path,
        "filename":      row.filename,
        "is_fake":       row.is_fake,
        "confidence":    row.confidence,
        "proba_cnn":     row.proba_cnn,
        "proba_lstm":    row.proba_lstm,
        "proba_bio":     row.proba_bio,
        "department":    row.department,
        "submitter":     row.submitter,
        "purpose":       row.purpose,
        "timestamp":     row.timestamp,
        "analysis_text": row.analysis_text,
        "report_path":   row.report_path,
        "risk_level":    row.risk_level,
        "risk_score":    row.risk_score,
    }


def create_case(db: Session, data: dict) -> AudioCase:
    """Insert a new audio case record."""
    case = AudioCase(**data)
    db.add(case)
    db.commit()
    db.refresh(case)
    return case


def get_case(db: Session, case_id: str) -> dict | None:
    """Fetch a single case by ID."""
    row = db.query(AudioCase).filter(AudioCase.case_id == case_id).first()
    return _row_to_dict(row) if row else None


def get_all_cases(db: Session) -> list[dict]:
    """Return all cases ordered newest-first."""
    rows = db.query(AudioCase).order_by(AudioCase.timestamp.desc()).all()
    return [_row_to_dict(r) for r in rows]


def get_cases_by_department(db: Session, department: str, days: int = 30) -> list[dict]:
    """Return cases for a department within the last N days."""
    cutoff = (datetime.now(timezone.utc) - timedelta(days=days)).isoformat()
    rows = (
        db.query(AudioCase)
        .filter(AudioCase.department == department, AudioCase.timestamp >= cutoff)
        .order_by(AudioCase.timestamp.desc())
        .all()
    )
    return [_row_to_dict(r) for r in rows]


def update_case_analysis(db: Session, case_id: str, updates: dict) -> None:
    """Update analysis fields on an existing case after agent processing."""
    db.query(AudioCase).filter(AudioCase.case_id == case_id).update(updates)
    db.commit()


def get_stats(db: Session) -> dict:
    """Return summary statistics for the dashboard header."""
    all_cases   = db.query(AudioCase).all()
    fake_cases  = [c for c in all_cases if c.is_fake]
    departments = {c.department for c in fake_cases if c.department}
    reports     = [c for c in all_cases if c.report_path]
    return {
        "total_cases":         len(all_cases),
        "deepfakes_detected":  len(fake_cases),
        "departments_targeted": len(departments),
        "reports_generated":   len(reports),
    }
