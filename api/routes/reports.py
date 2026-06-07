"""
Report retrieval routes — GET /reports/{case_id}, GET /reports/

NOTE: Order matters! The /reports/ list route MUST be registered before
the /reports/{case_id} catch-all, otherwise FastAPI would route /reports/
into get_report() and 404 with case_id="".
"""

import os
from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse

router = APIRouter(prefix="/reports", tags=["Reports"])

REPORTS_DIR = "./reports"


@router.get("/")
def list_reports():
    """List all available report files."""
    if not os.path.isdir(REPORTS_DIR):
        return []
    files = sorted(
        f for f in os.listdir(REPORTS_DIR) if f.endswith(".txt")
    )
    return [
        {
            "filename": f,
            "case_id":  f.replace("case_", "").replace(".txt", ""),
            "size_bytes": os.path.getsize(os.path.join(REPORTS_DIR, f)),
        }
        for f in files
    ]


@router.get("/{case_id}")
def get_report(case_id: str):
    """Download the audit report text file for a given case."""
    # Strip any accidental path traversal
    case_id = os.path.basename(case_id)
    path = os.path.join(REPORTS_DIR, f"case_{case_id}.txt")
    if not os.path.exists(path):
        raise HTTPException(
            status_code=404,
            detail=f"Report for case '{case_id}' not found. "
                   "Run a full analysis first to generate a report."
        )
    return FileResponse(
        path,
        media_type="text/plain; charset=utf-8",
        filename=f"voiceguard_report_{case_id}.txt",
    )
