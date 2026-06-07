import os
import sys
import uuid
from pathlib import Path
from functools import lru_cache

from dotenv import load_dotenv
load_dotenv()

from fastapi import APIRouter, File, Form, UploadFile, HTTPException
from fastapi.responses import FileResponse

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
    file:             UploadFile = File(None, description="Audio file to analyze (.wav/.mp3/.flac/.ogg/.m4a)"),
    inputType:        str        = Form("voice", description="Input type: 'voice' or 'text'"),
    textInput:        str        = Form("", description="Raw text input from the customer"),
    submitter:        str        = Form("", description="Name or email of the person submitting the ticket"),
    department:       str        = Form("", description="Department (Finance, Legal, Executive…)"),
    purpose:          str        = Form("", description="Purpose / description of the ticket"),
    outputPreference: str        = Form("text", description="Output response preference: 'text' or 'voice'"),
):
    """
    Full VoiceGuard customer support agent pipeline:
      1. If voice input: check deepfake signals.
         - If FAKE: activate security warning lock and store in Fraud Memory immediately.
         - If REAL: transcribe audio using Speech-to-Text.
      2. If text input or real voice: pass query to Customer Support Agent.
      3. Search historical customer interactions & memory engine.
      4. Synthesize personalized LLM agent response with sentiment tags.
      5. If voice output: convert response back to audio via Text-to-Speech.
      6. Return structured response.
    """
    tmp_path = None
    filename = ""

    # ── Handle Voice Input ─────────────────────────────────────────────────────
    if inputType == "voice":
        if not file or not file.filename:
            raise HTTPException(
                status_code=400,
                detail="An audio file must be uploaded when inputType is 'voice'."
            )
        
        suffix = Path(file.filename).suffix.lower()
        if suffix not in ALLOWED_EXTENSIONS:
            raise HTTPException(
                status_code=400,
                detail=f"Unsupported format '{suffix}'. Allowed: {sorted(ALLOWED_EXTENSIONS)}",
            )

        audio_bytes = await file.read()
        size_mb     = len(audio_bytes) / 1_000_000
        if size_mb > MAX_FILE_SIZE_MB:
            raise HTTPException(
                status_code=413,
                detail=f"File too large ({size_mb:.1f} MB). Maximum: {MAX_FILE_SIZE_MB} MB",
            )

        job_id   = str(uuid.uuid4())
        tmp_path = UPLOAD_DIR / f"{job_id}{suffix}"
        with open(tmp_path, "wb") as fh:
            fh.write(audio_bytes)
        filename = file.filename

    # ── Run agent pipeline ────────────────────────────────────────────────────
    try:
        context = {
            "submitter":  submitter.strip() or "Unknown",
            "department": department.strip() or "General",
            "purpose":    purpose.strip()    or "Not specified",
        }
        agent  = _get_agent()
        result = agent.analyze(
            audio_path=str(tmp_path) if tmp_path else None,
            filename=filename,
            context=context,
            input_type=inputType,
            text_input=textInput.strip(),
            output_preference=outputPreference
        )

    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Analysis failed: {exc}") from exc

    finally:
        # Clean up temp file regardless of outcome
        if tmp_path and tmp_path.exists():
            try:
                os.unlink(tmp_path)
            except OSError:
                pass

    return result


@router.get("/speech/{case_id}")
def get_speech(case_id: str):
    """Download the synthesized speech MP3 file for a case."""
    case_id = os.path.basename(case_id)
    REPORTS_DIR = ROOT / "reports"
    path = REPORTS_DIR / f"speech_{case_id}.mp3"
    if not path.exists():
        raise HTTPException(
            status_code=404,
            detail=f"Speech audio for case '{case_id}' not found."
        )
    return FileResponse(
        path,
        media_type="audio/mpeg",
        filename=f"speech_{case_id}.mp3"
    )

