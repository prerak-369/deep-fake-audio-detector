"""
Report retrieval routes — GET /reports/{case_id}
"""

import os
from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse

router = APIRouter(prefix="/reports", tags=["Reports"])

REPORTS_DIR = "./reports"


@router.get("/{case_id}")
def get_report(case_id: str):
    """Download the audit report text file for a given case."""
    path = os.path.join(REPORTS_DIR, f"case_{case_id}.txt")
    if not os.path.exists(path):
        raise HTTPException(status_code=404, detail=f"Report for case {case_id} not found")
    return FileResponse(
        path,
        media_type="text/plain",
        filename=f"voiceguard_report_{case_id}.txt",
    )


@router.get("/")
def list_reports():
    """List all available report files."""
    if not os.path.isdir(REPORTS_DIR):
        return []
    files = [f for f in os.listdir(REPORTS_DIR) if f.endswith(".txt")]
    return [{"filename": f, "case_id": f.replace("case_", "").replace(".txt", "")} for f in files]
