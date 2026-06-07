"""
seed_demo_data.py — Inserts 2 pre-dated fake Finance incidents so the
pattern engine fires on the very first demo run.

Run AFTER init_memory.py:
    python scripts/seed_demo_data.py

Safe to run multiple times — checks for existing case IDs before inserting.
"""

import sys
from pathlib import Path
from datetime import datetime, timedelta, timezone

ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT))

from api.database.connection import SessionLocal
from api.database import models  # noqa — triggers create_all
from api.database.crud import create_case, get_case

REPORTS_DIR = ROOT / "reports"


SEED_CASES = [
    {
        "case_id":       "DEMO0001",
        "audio_path":    "demo/past_incident_1.wav",
        "filename":      "cfo_approval_jan15.wav",
        "is_fake":       True,
        "confidence":    0.887,
        "proba_cnn":     0.901,
        "proba_lstm":    0.874,
        "proba_bio":     0.886,
        "department":    "Finance",
        "submitter":     "m.chen@acme.com",
        "purpose":       "CFO approving $1.8M wire transfer to Singapore account",
        "timestamp":     (datetime.now(timezone.utc) - timedelta(days=14)).isoformat(),
        "analysis_text": (
            "VERDICT: DEEPFAKE DETECTED with 88.7% confidence.\n\n"
            "REGULATORY EXPOSURE: Potential SOX Section 302 violation. "
            "Wire transfer halted pending investigation.\n\n"
            "IMMEDIATE ACTIONS: Transfer cancelled. Submitter account frozen. "
            "IT Security notified. SAR filed with FinCEN."
        ),
        "report_path":   "reports/case_DEMO0001.txt",
        "risk_level":    "CRITICAL",
        "risk_score":    9.4,
    },
    {
        "case_id":       "DEMO0002",
        "audio_path":    "demo/past_incident_2.wav",
        "filename":      "cfo_jan28_budget_approval.wav",
        "is_fake":       True,
        "confidence":    0.934,
        "proba_cnn":     0.951,
        "proba_lstm":    0.918,
        "proba_bio":     0.933,
        "department":    "Finance",
        "submitter":     "j.torres@acme.com",
        "purpose":       "CFO approving emergency budget reallocation $950K",
        "timestamp":     (datetime.now(timezone.utc) - timedelta(days=7)).isoformat(),
        "analysis_text": (
            "VERDICT: DEEPFAKE DETECTED with 93.4% confidence. "
            "Second incident in Finance department within 14 days.\n\n"
            "REGULATORY EXPOSURE: Coordinated attack pattern. "
            "GDPR Article 33 breach notification filed.\n\n"
            "PATTERN: Both incidents target high-value CFO authorisations in Finance. "
            "Escalated to Legal."
        ),
        "report_path":   "reports/case_DEMO0002.txt",
        "risk_level":    "CRITICAL",
        "risk_score":    9.7,
    },
]


def _write_demo_report(case: dict) -> None:
    """Write a minimal audit report file so GET /reports/ and downloads work."""
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    path = REPORTS_DIR / f"case_{case['case_id']}.txt"
    if path.exists():
        return
    content = f"""VoiceGuard Compliance Intelligence — Demo Audit Report
Case ID    : {case['case_id']}
Filename   : {case['filename']}
Department : {case['department']}
Submitter  : {case['submitter']}
Purpose    : {case['purpose']}
Timestamp  : {case['timestamp']}

DETECTION VERDICT
  DEEPFAKE DETECTED — {case['confidence'] * 100:.1f}% confidence
  CNN: {case['proba_cnn']}  LSTM: {case['proba_lstm']}  Bio: {case['proba_bio']}
  Risk: {case['risk_level']} ({case['risk_score']}/10)

AGENT ANALYSIS
{case['analysis_text']}
"""
    path.write_text(content.strip() + "\n", encoding="utf-8")


def seed():
    db = SessionLocal()
    inserted = 0
    skipped  = 0
    reports  = 0

    try:
        for case_data in SEED_CASES:
            _write_demo_report(case_data)
            reports += 1

            existing = get_case(db, case_data["case_id"])
            if existing:
                print(f"  ↩  {case_data['case_id']} already exists — skipping")
                skipped += 1
            else:
                create_case(db, case_data)
                print(f"  ✓  Inserted {case_data['case_id']} — {case_data['purpose'][:60]}")
                inserted += 1
    finally:
        db.close()

    print(f"\nSeeding complete: {inserted} inserted, {skipped} skipped, {reports} demo reports ensured.")
    if inserted > 0 or reports > 0:
        print("Pattern engine will now show 2 prior Finance incidents on first demo run.")


if __name__ == "__main__":
    print("=" * 60)
    print("VoiceGuard — Demo Data Seeding")
    print("=" * 60)
    seed()
