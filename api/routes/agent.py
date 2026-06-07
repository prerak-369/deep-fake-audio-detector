"""
Agent analysis route — POST /agent/analyze

Accepts a multipart upload: audio file + form fields (submitter, department, purpose).
Runs the full ComplianceAgent pipeline and returns a structured JSON response.
"""

import os
import sys
import uuid
from pathlib import Path
from functools import lru_cache

from dotenv import load_dotenv
load_dotenv()

from fastapi import APIRouter, File, Form, UploadFile, HTTPException

ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(ROOT))

from agent.compliance_agent import ComplianceAgent

router = APIRouter(prefix="/agent", tags=["Agent"])

ALLOWED_EXTENSIONS = {".wav", ".mp3", ".flac", ".ogg", ".m4a"}
MAX_FILE_SIZE_MB   = 10

# Upload temp directory
UPLOAD_DIR = ROOT / "data" / "uploads"
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)


@lru_cache(maxsize=1)
def _get_agent() -> ComplianceAgent:
    """Singleton ComplianceAgent — loaded once, reused forever."""
    return ComplianceAgent()


@router.post("/analyze")
async def agent_analyze(
    file:              UploadFile = File(...,  description="Audio file to analyse (.wav/.mp3/.flac/.ogg/.m4a)"),
    submitter:         str        = Form("",   description="Name or email of the person submitting the audio"),
    department:        str        = Form("",   description="Department (Finance, Legal, Executive…)"),
    purpose:           str        = Form("",   description="Purpose / description of the audio recording"),
    issue_description: str        = Form("",   description="Written details of the customer issue"),
):
    """
    Full compliance pipeline:
      1. Validate and save uploaded audio
      2. Run CNN/LSTM/Biometrics deepfake detection
      3. Store in episodic memory
      4. Query regulatory knowledge base
      5. Run historical pattern engine
      6. Compute risk score
      7. Generate LLM analysis (GPT-4o or rule-based fallback)
      8. Write audit report
      9. Return full structured result
    """
    # ── Validate format ────────────────────────────────────────────────────────
    suffix = Path(file.filename or "").suffix.lower()
    if suffix not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported format '{suffix}'. Allowed: {sorted(ALLOWED_EXTENSIONS)}",
        )

    # ── Read and size-check ────────────────────────────────────────────────────
    audio_bytes = await file.read()
    size_mb     = len(audio_bytes) / 1_000_000
    if size_mb > MAX_FILE_SIZE_MB:
        raise HTTPException(
            status_code=413,
            detail=f"File too large ({size_mb:.1f} MB). Maximum: {MAX_FILE_SIZE_MB} MB",
        )

    # ── Save to temp dir ───────────────────────────────────────────────────────
    job_id   = str(uuid.uuid4())
    tmp_path = UPLOAD_DIR / f"{job_id}{suffix}"
    try:
        with open(tmp_path, "wb") as fh:
            fh.write(audio_bytes)

        # ── Run agent ─────────────────────────────────────────────────────────
        context = {
            "submitter":         submitter.strip() or "Unknown",
            "department":        department.strip() or "General",
            "purpose":           purpose.strip()    or "Not specified",
            "issue_description": issue_description.strip() or "",
        }
        agent  = _get_agent()
        result = agent.analyze(
            audio_path=str(tmp_path),
            filename=file.filename or f"upload{suffix}",
            context=context,
        )

    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Analysis failed: {exc}") from exc

    finally:
        # Clean up temp file regardless of outcome
        try:
            os.unlink(tmp_path)
        except OSError:
            pass

    return result
