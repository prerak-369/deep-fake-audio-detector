"""
Episodic memory — structured record of every detection case in SQLite.
Uses a fresh DB session per call so it can be used outside of FastAPI's request context.
"""

import uuid
from datetime import datetime, timezone

from api.database.connection import SessionLocal
from api.database import crud


class EpisodicMemory:
    """Read/write access to the audio_cases table."""

    def store_detection(self, audio_path: str, filename: str, detection: dict, context: dict) -> str:
        """
        Persist a new detection result immediately after inference.
        Returns the generated case_id.
        """
        case_id = str(uuid.uuid4())[:8].upper()
        db = SessionLocal()
        try:
            crud.create_case(db, {
                "case_id":      case_id,
                "audio_path":   audio_path,
                "filename":     filename,
                "is_fake":      detection["is_fake"],
                "confidence":   detection["confidence"],
                "proba_cnn":    detection.get("proba_cnn"),
                "proba_lstm":   detection.get("proba_lstm"),
                "proba_bio":    detection.get("proba_bio"),
                "department":   context.get("department"),
                "submitter":    context.get("submitter"),
                "purpose":      context.get("purpose"),
                "timestamp":    datetime.now(timezone.utc).isoformat(),
            })
        finally:
            db.close()
        return case_id

    def update_case(self, case_id: str, analysis: str, report: dict, risk: dict) -> None:
        """Append agent analysis, report path, and risk metadata to an existing case."""
        db = SessionLocal()
        try:
            crud.update_case_analysis(db, case_id, {
                "analysis_text": analysis,
                "report_path":   report.get("url"),
                "risk_level":    risk["level"],
                "risk_score":    risk["score"],
            })
        finally:
            db.close()

    def get_recent_by_department(self, department: str, days: int = 30) -> list:
        """Return recent cases for a given department (for pattern analysis)."""
        db = SessionLocal()
        try:
            return crud.get_cases_by_department(db, department, days)
        finally:
            db.close()

    def get_all(self) -> list:
        """Return all cases — used by the dashboard memory explorer."""
        db = SessionLocal()
        try:
            return crud.get_all_cases(db)
        finally:
            db.close()
