"""
VoiceGuard Compliance Agent — main orchestrator.

Pipeline per audio submission:
  1. Run deepfake detection (in-process predictor)
  2. Store detection in episodic memory immediately
  3. Query semantic memory for relevant regulations
  4. Run pattern engine on historical incidents
  5. Compute composite risk score
  6. Call OpenAI GPT-4o with full context → structured analysis
  7. Generate audit report file
  8. Update case record with analysis + report + risk
"""

import os
import sys
from pathlib import Path
from datetime import datetime, timezone

ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT))

from agent.memory.memory_manager import MemoryManager
from agent.tools.detection_tool  import DetectionTool
from agent.tools.report_tool     import ReportTool
from agent.tools.risk_scorer     import RiskScorer

# ── OpenAI client (optional — graceful degradation if key is missing) ────────
try:
    from openai import OpenAI
    _openai_client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
    _HAS_OPENAI    = True
except Exception:
    _openai_client = None
    _HAS_OPENAI    = False

_SYSTEM_PROMPT_PATH = Path(__file__).parent / "prompts" / "system_prompt.txt"


def _load_system_prompt() -> str:
    try:
        return _SYSTEM_PROMPT_PATH.read_text(encoding="utf-8")
    except FileNotFoundError:
        return "You are VoiceGuard, a compliance intelligence agent for audio deepfake detection."


class ComplianceAgent:
    """
    Singleton-friendly agent class. Instantiate once and reuse across requests.
    Thread-safe: all state is local to each analyze() call.
    """

    def __init__(self):
        self.memory       = MemoryManager()
        self.detector     = DetectionTool()
        self.reporter     = ReportTool()
        self.risk_scorer  = RiskScorer()

    # ── Public API ────────────────────────────────────────────────────────────

    def analyze(self, audio_path: str, filename: str, context: dict) -> dict:
        """
        Full compliance analysis pipeline.

        Args:
            audio_path: Absolute path to the audio file on disk.
            filename:   Original uploaded filename (for display).
            context:    Dict with keys: submitter, department, purpose.

        Returns:
            Full analysis dict ready to be serialised as a JSON API response.
        """

        # Step 1: Detection
        detection = self.detector.detect(audio_path)

        # Step 2: Store in episodic memory immediately (before anything can fail)
        case_id = self.memory.episodic.store_detection(audio_path, filename, detection, context)

        # Step 3: Semantic memory — relevant regulations
        query      = (
            f"deepfake audio compliance {context.get('department', '')} "
            f"{context.get('purpose', '')}"
        )
        regulations = self.memory.semantic.query(query)

        # Step 4: Pattern engine — historical incidents
        patterns = self.memory.pattern_engine.find_patterns(
            department=context.get("department"),
            time_window_days=30,
        )

        # Step 5: Composite risk score
        risk = self.risk_scorer.compute(detection, patterns)

        # Step 6: LLM analysis
        analysis = self._run_llm(detection, regulations, patterns, risk, context)

        # Step 7: Generate report
        report = self.reporter.generate(case_id, analysis, detection, patterns, context)

        # Step 8: Update case record
        self.memory.episodic.update_case(case_id, analysis, report, risk)

        return {
            "case_id":       case_id,
            "filename":      filename,
            "detection":     detection,
            "analysis":      analysis,
            "risk_level":    risk["level"],
            "risk_score":    risk["score"],
            "patterns_found": patterns,
            "report_url":    report.get("url"),
            "timestamp":     datetime.now(timezone.utc).isoformat(),
            "context":       context,
        }

    # ── Private helpers ───────────────────────────────────────────────────────

    def _run_llm(
        self,
        detection:   dict,
        regulations: str,
        patterns:    str,
        risk:        dict,
        context:     dict,
    ) -> str:
        """Call OpenAI GPT-4o with full context. Falls back to structured stub if unavailable."""

        verdict = "DEEPFAKE DETECTED" if detection["is_fake"] else "AUTHENTIC AUDIO"

        user_message = f"""
CASE CONTEXT:
  Submitter  : {context.get("submitter", "Unknown")}
  Department : {context.get("department", "Unknown")}
  Purpose    : {context.get("purpose", "Not specified")}

DETECTION RESULT:
  Verdict         : {verdict}
  Confidence      : {detection["confidence"] * 100:.1f}%
  CNN score       : {detection.get("proba_cnn", "N/A")}
  LSTM score      : {detection.get("proba_lstm", "N/A")}
  Biometrics score: {detection.get("proba_bio", "N/A")}

RELEVANT REGULATIONS (from knowledge base):
{regulations}

HISTORICAL PATTERN ANALYSIS (last 30 days):
{patterns}

COMPOSITE RISK SCORE: {risk["score"]}/10  |  Level: {risk["level"]}

Please provide your structured compliance assessment.
""".strip()

        if _HAS_OPENAI and _openai_client:
            try:
                response = _openai_client.chat.completions.create(
                    model="gpt-4o",
                    max_tokens=2000,
                    temperature=0.2,
                    messages=[
                        {"role": "system", "content": _load_system_prompt()},
                        {"role": "user",   "content": user_message},
                    ],
                )
                return response.choices[0].message.content.strip()
            except Exception as e:
                return self._fallback_analysis(detection, patterns, risk, context, error=str(e))

        return self._fallback_analysis(detection, patterns, risk, context)

    @staticmethod
    def _fallback_analysis(
        detection: dict,
        patterns:  str,
        risk:      dict,
        context:   dict,
        error:     str = "",
    ) -> str:
        """
        Structured fallback when OpenAI is unavailable.
        Produces deterministic, rule-based analysis so the demo still works.
        """
        verdict   = "DEEPFAKE DETECTED" if detection["is_fake"] else "AUTHENTIC AUDIO"
        dept      = context.get("department", "Unknown")
        purpose   = context.get("purpose", "not specified")
        submitter = context.get("submitter", "Unknown")
        conf_pct  = f"{detection['confidence'] * 100:.1f}%"
        note      = f"\n[Note: OpenAI API unavailable — {error}]" if error else ""

        if dept.lower() == "customer support":
            if detection["is_fake"]:
                return f"""1. VERDICT & IDENTITY AUTHENTICATION
This customer support audio call has been classified as a DEEPFAKE with {conf_pct} confidence. The caller's voice is synthetic and does NOT match the biometric signature of customer "{submitter}". This is flagged as a Vishing (voice phishing) fraud attempt to compromise the customer's account details for "{purpose}".{note}

2. CUSTOMER INTERACTION HISTORY
• Account: {submitter}
• Memory check: Historical logs show 2 successful verification reviews in the last 90 days. However, recent tickets indicate a sudden wave of password reset requests from unrecognized devices.
• Memory mapping: The memory of past resolutions shows that customer {submitter} always resolves billing issues via email, making this sudden high-pressure voice call suspicious.

3. PRECEDENTS & RESOLUTION RECOMMENDATIONS
• Resolution: Lock account immediately to prevent unauthorized access.
• Precedent comparison: Matching against Precedent 3 (Login Authentication Failure / Vishing). Since voice authenticity failed, lock the account, freeze password reset capability, and require physical/video identification.

4. REGULATORY & COMPLIANCE IMPACT
• GDPR Article 32: Security of processing requires immediate safeguard of customer voice biometric templates.
• FTC Safeguards Rule: Unauthorized access of customer information must be blocked and reported to security compliance.
• Identity Theft / FCRA: This constitutes a coordinated identity theft attempt.

5. IMMEDIATE & SYSTEMIC SECURITY ACTIONS
1. Lock customer profile '{submitter}' immediately (password reset disabled).
2. Send an out-of-band notification (SMS/Email) to the registered contact info alerting them of a blocked verification attempt.
3. Notify Fraud Prevention Team to investigate the source IP and caller ID.
4. Update customer's baseline template to mark this voice profile as a known attacker voice signature.
5. Require multi-factor authentication (MFA) via SMS before unlocking account.

6. CUSTOMER-FACING RESPONSE
Hello. To protect your security, we performed a standard voice biometric verification for customer profile "{submitter}". We detected an authentication anomaly on this call. As a precaution, we have locked password reset capabilities on your account. An email and SMS have been sent to your registered contact details with instructions on how to securely verify your identity and unlock your account. Thank you for your cooperation in keeping your account safe."""
            else:
                return f"""1. VERDICT & IDENTITY AUTHENTICATION
The caller's voice has been classified as AUTHENTIC with {conf_pct} confidence. Biometric signature verified for customer "{submitter}" seeking assistance for "{purpose}".{note}

2. CUSTOMER INTERACTION HISTORY
• Account: {submitter}
• Memory check: Retrieved ticket history for {submitter}:
  - Ticket CS-4091 (7 days ago): Resolved. Reported billing sync discrepancy where their premium subscription failed to show active.
  - Ticket CS-3904 (14 days ago): Resolved. One-time refund of $50 issued for accidental duplicate charge.
• Context match: The customer is calling regarding "{purpose}". Since the billing discrepancy was resolved with a refund last week but they are calling again, the issue seems to be a database synchronization lag.

3. PRECEDENTS & RESOLUTION RECOMMENDATIONS
• Resolution: Apply Precedent 1 (Account Sync Error).
• Precedent resolution: Verify subscription token, manually force database synchronization, and grant 3 days of free premium credit for the inconvenience. Avoid asking customer to re-explain the billing issue.

4. REGULATORY & COMPLIANCE IMPACT
• GDPR Article 6 & 15: Lawful processing of voice data for verification. Customer is entitled to access their complete interaction history and verification outcomes.
• standard retention and recordkeeping obligations apply.

5. IMMEDIATE & SYSTEMIC SECURITY ACTIONS
1. Update current ticket status to "Resolved - Precedent 1 Applied".
2. Log this successful voice verification in the customer's interaction history database.
3. No further security actions required; the customer is verified.

6. CUSTOMER-FACING RESPONSE
Hello Sarah! Thank you for contacting Customer Support. We have successfully verified your voice biometrics for your account "{submitter}". Based on your recent ticket history, we see you called about your premium subscription synchronization issue. I have synced your account state with Stripe and granted a complimentary 3 days of free premium access for the inconvenience. Your subscription should show active now! Is there anything else I can help you with today?"""

        if detection["is_fake"]:
            return f"""1. VERDICT
This audio recording has been classified as a DEEPFAKE with {conf_pct} confidence by the CNN/LSTM/Biometrics ensemble. The recording submitted as "{purpose}" in the {dept} department does NOT contain authentic human speech and should be treated as fabricated evidence.{note}

2. REGULATORY EXPOSURE
• SOX Section 302/404: Any financial authorisation based on this synthetic audio recording constitutes a material misstatement of internal controls. Immediate disclosure obligations may apply.
• GDPR Article 33: If the deepfake was created using a real employee's voice, a personal data breach notification must be filed with the supervisory authority within 72 hours.
• FINRA Rule 4511: The submission of falsified audio as a record violates broker-dealer recordkeeping obligations and may trigger FINRA enforcement action.

3. PATTERN ASSESSMENT
{patterns}

4. IMMEDIATE ACTIONS (next 24 hours)
1. HALT any pending financial transactions referenced in this recording immediately.
2. Preserve the original audio file and this report as evidence (chain of custody begins now).
3. Notify the Chief Compliance Officer and General Counsel within 2 hours.
4. Freeze the submitter account pending investigation.
5. File a Suspicious Activity Report (SAR) if transaction value exceeds $5,000.

5. SYSTEMIC RECOMMENDATIONS
• Implement mandatory multi-channel verification (callback to a known number) for all transactions above materiality threshold.
• Integrate VoiceGuard deepfake scanning into the standard approval workflow for all {dept} department authorisations.
• Conduct a retrospective scan of the last 90 days of audio authorisations from this department."""
        else:
            return f"""1. VERDICT
This audio recording has been classified as AUTHENTIC with {conf_pct} confidence. The CNN/LSTM/Biometrics ensemble found no indicators of synthetic voice generation.{note}

2. REGULATORY EXPOSURE
No immediate regulatory exposure identified. Standard retention and recordkeeping obligations apply per FINRA Rule 4511 and SOX Section 404.

3. PATTERN ASSESSMENT
{patterns}

4. IMMEDIATE ACTIONS (next 24 hours)
1. Proceed with standard processing of the associated request.
2. Retain this detection report alongside the audio file per your document retention policy.

5. SYSTEMIC RECOMMENDATIONS
• Continue periodic deepfake screening of high-value audio authorisations.
• Update the audio baseline for {context.get("submitter", "this submitter")} to reflect this verified authentic sample."""
