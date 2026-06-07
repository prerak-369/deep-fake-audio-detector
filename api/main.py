"""
FastAPI Backend — VoiceGuard Compliance Intelligence Agent
==========================================================
Endpoints (existing):
  POST /analyze        upload audio file → returns job_id
  GET  /result/{id}    get prediction result
  GET  /health         health check

Endpoints (new — VoiceGuard agent layer):
  POST /agent/analyze          full compliance analysis
  GET  /memory/history         case history
  GET  /memory/case/{id}       single case
  GET  /memory/patterns        pattern analysis
  GET  /memory/stats           dashboard stats
  GET  /reports/{case_id}      download audit report
  GET  /reports/               list all reports

Run:
  uvicorn api.main:app --reload --port 8000
"""

import uuid
import time
import sys
from pathlib import Path
from typing import Dict

from dotenv import load_dotenv

load_dotenv()

from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import RedirectResponse
from fastapi.staticfiles import StaticFiles

ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT))

from api.schemas.request  import AnalyzeResponse, ResultResponse, HealthResponse
from api.predictor        import get_predictor
from src.utils.logger     import get_logger

# ── New routers ───────────────────────────────────────────────────────────────
from api.routes.agent   import router as agent_router
from api.routes.memory  import router as memory_router
from api.routes.reports import router as reports_router

logger = get_logger("api")

app = FastAPI(
    title="VoiceGuard Compliance Intelligence Agent",
    description="AI-powered audio deepfake detection with memory, pattern analysis, and regulatory reporting.",
    version="2.0.0",
)

# ── CORS ──────────────────────────────────────────────────────────────────────
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Mount new routers ─────────────────────────────────────────────────────────
app.include_router(agent_router)
app.include_router(memory_router)
app.include_router(reports_router)

# ── Serve frontend static files ───────────────────────────────────────────────
frontend_dir = ROOT / "frontend"
if frontend_dir.exists():
    app.mount("/static", StaticFiles(directory=str(frontend_dir)), name="static")

# ── In-memory result store (existing behaviour unchanged) ─────────────────────
results: Dict[str, dict] = {}

ALLOWED_EXTENSIONS = {".wav", ".mp3", ".flac", ".ogg", ".m4a"}
MAX_FILE_SIZE_MB   = 10


@app.get("/")
def root():
    """Redirect browser visits to the VoiceGuard dashboard."""
    return RedirectResponse(url="/static/dashboard.html")


@app.get("/health", response_model=HealthResponse)
def health():
    """Check if the API and model are ready."""
    predictor = get_predictor()
    return HealthResponse(status="ok", model_loaded=predictor.is_ready())


@app.post("/analyze", response_model=AnalyzeResponse)
async def analyze(file: UploadFile = File(...)):
    """
    Upload an audio file and get a job_id.
    Poll GET /result/{job_id} for the verdict.
    """
    suffix = Path(file.filename).suffix.lower()
    if suffix not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported format '{suffix}'. Allowed: {ALLOWED_EXTENSIONS}"
        )

    audio_bytes = await file.read()
    size_mb = len(audio_bytes) / 1e6
    if size_mb > MAX_FILE_SIZE_MB:
        raise HTTPException(
            status_code=413,
            detail=f"File too large ({size_mb:.1f} MB). Max: {MAX_FILE_SIZE_MB} MB"
        )

    job_id   = str(uuid.uuid4())
    tmp_dir  = ROOT / "data" / "uploads"
    tmp_dir.mkdir(parents=True, exist_ok=True)
    tmp_path = tmp_dir / f"{job_id}{suffix}"

    with open(tmp_path, "wb") as f:
        f.write(audio_bytes)

    try:
        t_start   = time.time()
        predictor = get_predictor()
        result    = predictor.predict(str(tmp_path))
        elapsed   = round((time.time() - t_start) * 1000, 1)

        results[job_id] = {
            "job_id":       job_id,
            "filename":     file.filename,
            "verdict":      result["verdict"],
            "confidence":   result["confidence"],
            "proba_cnn":    result["proba_cnn"],
            "proba_lstm":   result["proba_lstm"],
            "proba_bio":    result["proba_bio"],
            "duration_sec": result["duration_sec"],
            "inference_ms": elapsed,
            "status":       "done",
        }
        logger.info(f"[{job_id[:8]}] {file.filename} → {result['verdict']} "
                    f"({result['confidence']*100:.1f}%) in {elapsed}ms")

    except Exception as e:
        results[job_id] = {"status": "error", "error": str(e)}
        logger.error(f"[{job_id[:8]}] Inference failed: {e}")
    finally:
        try:
            tmp_path.unlink()
        except Exception:
            pass

    return AnalyzeResponse(job_id=job_id, status=results[job_id]["status"])


@app.get("/result/{job_id}", response_model=ResultResponse)
def get_result(job_id: str):
    """Get the prediction result for a job_id."""
    if job_id not in results:
        raise HTTPException(status_code=404, detail="Job not found")

    r = results[job_id]
    if r["status"] == "error":
        raise HTTPException(status_code=500, detail=r.get("error", "Unknown error"))

    return ResultResponse(**r)