"""
Agent analysis route — POST /agent/analyze
Accepts a multipart form: audio file + context fields.
"""

import shutil
import tempfile
from pathlib import Path

from fastapi import APIRouter, UploadFile, File, Form, HTTPException
from agent.compliance_agent import ComplianceAgent

router = APIRouter(prefix="/agent", tags=["Agent"])

# Singleton agent — loaded once, reused across all requests
_agent = ComplianceAgent()

ALLOWED_EXTENSIONS = {".wav", ".mp3", ".flac", ".ogg", ".m4a"}
MAX_FILE_SIZE_MB   = 10


@router.post("/analyze")
def analyze_audio(
    file:        UploadFile = File(...),
    submitter:   str = Form(default="Unknown"),
    department:  str = Form(default="Unknown"),
    purpose:     str = Form(default="Not specified"),
):
    """
    Submit an audio file for full compliance analysis.

    Returns detection result, agent analysis, pattern history,
    risk score, and report file path.
    """
    suffix = Path(file.filename).suffix.lower()
    if suffix not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported format '{suffix}'. Allowed: {ALLOWED_EXTENSIONS}",
        )

    audio_bytes = file.file.read()
    if len(audio_bytes) / 1e6 > MAX_FILE_SIZE_MB:
        raise HTTPException(
            status_code=413,
            detail=f"File too large. Max: {MAX_FILE_SIZE_MB} MB",
        )

    # Save to a temp file (predictor needs a file path)
    with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
        tmp.write(audio_bytes)
        tmp_path = tmp.name

    context = {
        "submitter":  submitter,
        "department": department,
        "purpose":    purpose,
    }

    try:
        result = _agent.analyze(tmp_path, file.filename, context)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Analysis failed: {e}")
    finally:
        try:
            Path(tmp_path).unlink()
        except Exception:
            pass

    return result
