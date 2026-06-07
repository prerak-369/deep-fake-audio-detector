"""
Report tool — generates a plain-text audit report saved to ./reports/
Returns {"url": path, "case_id": id} for storage in episodic memory.
"""

import os
from datetime import datetime, timezone

REPORTS_DIR = "./reports"
os.makedirs(REPORTS_DIR, exist_ok=True)


class ReportTool:
    def generate(
        self,
        case_id: str,
        analysis: str,
        detection: dict,
        patterns: str,
        context: dict,
    ) -> dict:
        """Write a structured audit report to disk and return its path."""

        verdict  = "⚠ ESCALATED TICKET" if detection["is_fake"] else "✓ ROUTINE RESOLUTION"
        conf_pct = f"{detection['confidence'] * 100:.1f}%"
        ts       = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")

        content = f"""
╔══════════════════════════════════════════════════════════════════╗
║          VoiceGuard Support Intelligence — Resolution Report      ║
╚══════════════════════════════════════════════════════════════════╝

Case ID    : {case_id}
Generated  : {ts}
Submitter  : {context.get("submitter", "Unknown")}
Department : {context.get("department", "Unknown")}
Purpose    : {context.get("purpose", "Not specified")}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
DETECTION VERDICT
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

  {verdict}
  Ensemble Confidence : {conf_pct}
  CNN Score           : {detection.get("proba_cnn", "N/A")}
  LSTM Score          : {detection.get("proba_lstm", "N/A")}
  Biometrics Score    : {detection.get("proba_bio", "N/A")}
  Audio Duration      : {detection.get("duration_sec", "N/A")}s

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
HISTORICAL PATTERN ANALYSIS
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

{patterns or "No relevant historical incidents found."}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
AGENT ANALYSIS & REGULATORY ASSESSMENT
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

{analysis}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
This report was generated automatically by VoiceGuard v2.0.
Chain of custody: report saved at {ts}.
For regulatory queries contact your Compliance Officer.
"""

        report_path = os.path.join(REPORTS_DIR, f"case_{case_id}.txt")
        with open(report_path, "w", encoding="utf-8") as f:
            f.write(content.strip())

        return {"url": report_path, "case_id": case_id}
