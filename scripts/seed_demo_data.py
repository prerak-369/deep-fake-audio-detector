# -*- coding: utf-8 -*-
"""
seed_demo_data.py - Inserts 2 pre-dated fake Finance incidents so the
pattern engine fires on the very first demo run.

Run AFTER init_memory.py:
    python scripts/seed_demo_data.py

Safe to run multiple times - checks for existing case IDs before inserting.
Also writes stub audit-report .txt files for DEMO0001 and DEMO0002 so that
GET /reports/DEMO0001 returns a valid response during the demo.
"""

import os
import sys
from pathlib import Path
from datetime import datetime, timedelta, timezone

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT))

from api.database.connection import SessionLocal
from api.database import models  # noqa — triggers create_all
from api.database.crud import create_case, get_case


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
            "1. VERDICT\n"
            "DEEPFAKE DETECTED with 88.7% confidence.\n\n"
            "2. REGULATORY EXPOSURE\n"
            "Potential SOX Section 302 violation. "
            "Wire transfer halted pending investigation.\n\n"
            "3. PATTERN ASSESSMENT\n"
            "First incident detected in Finance department.\n\n"
            "4. IMMEDIATE ACTIONS\n"
            "Transfer cancelled. Submitter account frozen. "
            "IT Security notified. SAR filed with FinCEN.\n\n"
            "5. SYSTEMIC RECOMMENDATIONS\n"
            "Implement mandatory multi-channel verification for all "
            "Finance department transactions above materiality threshold."
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
            "1. VERDICT\n"
            "DEEPFAKE DETECTED with 93.4% confidence. "
            "Second incident in Finance department within 14 days.\n\n"
            "2. REGULATORY EXPOSURE\n"
            "Coordinated attack pattern. "
            "GDPR Article 33 breach notification filed.\n\n"
            "3. PATTERN ASSESSMENT\n"
            "PATTERN ALERT — 2 deepfake incidents targeting Finance in the last 30 days. "
            "Both incidents target high-value CFO authorisations. Escalated to Legal.\n\n"
            "4. IMMEDIATE ACTIONS\n"
            "Budget reallocation blocked. Both submitter accounts suspended. "
            "Board notified. External forensics engaged.\n\n"
            "5. SYSTEMIC RECOMMENDATIONS\n"
            "Integrate VoiceGuard scanning into the standard Finance approval workflow."
        ),
        "report_path":   "reports/case_DEMO0002.txt",
        "risk_level":    "CRITICAL",
        "risk_score":    9.7,
    },
    {
        "case_id":       "DEMO0003",
        "audio_path":    "demo/past_incident_3.wav",
        "filename":      "support_verification_jenkins.wav",
        "is_fake":       False,
        "confidence":    0.984,
        "proba_cnn":     0.012,
        "proba_lstm":    0.021,
        "proba_bio":     0.015,
        "department":    "Customer Support",
        "submitter":     "s.jenkins@gmail.com",
        "purpose":       "Customer Sarah Jenkins requesting subscription billing sync check",
        "timestamp":     (datetime.now(timezone.utc) - timedelta(days=5)).isoformat(),
        "analysis_text": (
            "1. VERDICT & IDENTITY AUTHENTICATION\n"
            "AUTHENTIC CUSTOMER AUDIO with 98.4% confidence. Voice signature verified for customer \"s.jenkins@gmail.com\".\n\n"
            "2. CUSTOMER INTERACTION HISTORY\n"
            "• Account: s.jenkins@gmail.com\n"
            "• Memory check: Customer has a history of 2 billing-related tickets in the last 14 days.\n\n"
            "3. PRECEDENTS & RESOLUTION RECOMMENDATIONS\n"
            "• Resolution: Apply Precedent 1 (Account Sync Error) to manually sync the Stripe token and credit 3 days of premium access.\n\n"
            "4. REGULATORY & COMPLIANCE IMPACT\n"
            "Lawful data verification processed in compliance with GDPR data protection requirements.\n\n"
            "5. IMMEDIATE & SYSTEMIC SECURITY ACTIONS\n"
            "No security escalation required. Logged successful verification in interaction logs."
        ),
        "report_path":   "reports/case_DEMO0003.txt",
        "risk_level":    "LOW",
        "risk_score":    1.2,
    },
    {
        "case_id":       "DEMO0004",
        "audio_path":    "demo/past_incident_4.wav",
        "filename":      "support_verification_spoof.wav",
        "is_fake":       True,
        "confidence":    0.912,
        "proba_cnn":     0.925,
        "proba_lstm":    0.898,
        "proba_bio":     0.914,
        "department":    "Customer Support",
        "submitter":     "d.miller@yahoo.com",
        "purpose":       "Bypass login locks and reset password via voice request",
        "timestamp":     (datetime.now(timezone.utc) - timedelta(days=2)).isoformat(),
        "analysis_text": (
            "1. VERDICT & IDENTITY AUTHENTICATION\n"
            "DEEPFAKE DETECTED (Vishing/Fraud Attempt) with 91.2% confidence. Voice is synthetic and does not match customer \"d.miller@yahoo.com\".\n\n"
            "2. CUSTOMER INTERACTION HISTORY\n"
            "• Account: d.miller@yahoo.com\n"
            "• Memory check: Third failed authentication attempt targeting David Miller's account in the last 7 days.\n\n"
            "3. PRECEDENTS & RESOLUTION RECOMMENDATIONS\n"
            "• Resolution: Trigger Precedent 3 (Vishing lockout). Lock account immediately and suspend password reset function.\n\n"
            "4. REGULATORY & COMPLIANCE IMPACT\n"
            "GDPR Article 32 personal data breach threat. High risk of unauthorized disclosure.\n\n"
            "5. IMMEDIATE & SYSTEMIC SECURITY ACTIONS\n"
            "Freeze account profile immediately. Notify the customer via secondary SMS/Email. Escalate to Support Security team."
        ),
        "report_path":   "reports/case_DEMO0004.txt",
        "risk_level":    "CRITICAL",
        "risk_score":    8.8,
    },
]


def write_demo_report(case: dict) -> None:
    """Write a stub audit report text file for a seeded demo case."""
    os.makedirs("reports", exist_ok=True)
    report_path = f"reports/case_{case['case_id']}.txt"
    if os.path.exists(report_path):
        return  # already exists, skip

    ts = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
    content = f"""
==================================================================
          VoiceGuard Compliance Intelligence - Audit Report
==================================================================

Case ID    : {case['case_id']}
Generated  : {ts}  [DEMO - pre-seeded incident]
Submitter  : {case['submitter']}
Department : {case['department']}
Purpose    : {case['purpose']}

------------------------------------------------------------------
DETECTION VERDICT
------------------------------------------------------------------

  ! DEEPFAKE DETECTED
  Ensemble Confidence : {case['confidence']*100:.1f}%
  CNN Score           : {case['proba_cnn']}
  LSTM Score          : {case['proba_lstm']}
  Biometrics Score    : {case['proba_bio']}
  Risk Level          : {case['risk_level']}
  Risk Score          : {case['risk_score']}/10

------------------------------------------------------------------
AGENT ANALYSIS & REGULATORY ASSESSMENT
------------------------------------------------------------------

{case['analysis_text']}

------------------------------------------------------------------
This report was generated automatically by VoiceGuard v2.0.
For regulatory queries contact your Compliance Officer.
""".strip()

    with open(report_path, "w", encoding="utf-8") as f:
        f.write(content)
    print(f"  [OK] Report written -> {report_path}")


def seed():
    db = SessionLocal()
    inserted = 0
    skipped  = 0

    try:
        for case_data in SEED_CASES:
            existing = get_case(db, case_data["case_id"])
            if existing:
                print(f"  [SKIP] {case_data['case_id']} already exists - skipping DB insert")
                skipped += 1
            else:
                create_case(db, case_data)
                print(f"  [OK] Inserted {case_data['case_id']} - " + case_data['purpose'][:60])
                inserted += 1

            # Always ensure the report file exists (idempotent)
            write_demo_report(case_data)

    finally:
        db.close()

    print(f"\nSeeding complete: {inserted} inserted, {skipped} skipped.")
    if inserted > 0 or skipped > 0:
        print("Pattern engine will now show 2 prior Finance incidents on first demo run.")


if __name__ == "__main__":
    print("=" * 60)
    print("VoiceGuard - Demo Data Seeding")
    print("=" * 60)
    seed()
