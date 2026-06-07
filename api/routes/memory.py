"""
Memory query routes — GET /memory/history, /memory/case/{id}, /memory/patterns, /memory/stats
"""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from api.database.connection import get_db
from api.database import crud
from agent.memory.pattern_engine import PatternEngine
from agent.memory.episodic       import EpisodicMemory

router = APIRouter(prefix="/memory", tags=["Memory"])

_episodic = EpisodicMemory()
_pattern  = PatternEngine(_episodic)


@router.get("/history")
def get_history(
    department: str | None = None,
    days:       int        = 30,
    db:         Session    = Depends(get_db),
):
    """Return case history, optionally filtered by department and time window."""
    if department:
        return crud.get_cases_by_department(db, department, days)
    return crud.get_all_cases(db)


@router.get("/case/{case_id}")
def get_case(case_id: str, db: Session = Depends(get_db)):
    """Return a single case record by ID."""
    case = crud.get_case(db, case_id)
    if not case:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail=f"Case {case_id} not found")
    return case


@router.get("/patterns")
def get_patterns(
    department: str | None = None,
    days:       int        = 30,
):
    """Return pattern analysis string for a department (or generic if omitted)."""
    pattern_text = _pattern.find_patterns(department=department, time_window_days=days)
    return {"department": department, "days": days, "analysis": pattern_text}


@router.get("/stats")
def get_stats(db: Session = Depends(get_db)):
    """Return summary statistics for the dashboard header cards."""
    return crud.get_stats(db)
