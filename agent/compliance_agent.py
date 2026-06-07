import os
import sys
import re
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
REPORTS_DIR = ROOT / "reports"
REPORTS_DIR.mkdir(parents=True, exist_ok=True)


def _load_system_prompt() -> str:
    try:
        return _SYSTEM_PROMPT_PATH.read_text(encoding="utf-8")
    except FileNotFoundError:
        return "You are VoiceGuard, a compliance intelligence agent for audio deepfake detection."


class ComplianceAgent:
    """
    Unified Support & Compliance Agent.
    Implements:
      - Voice Input: runs Deepfake detection → if FAKE, logs to Fraud Memory & triggers Security Warning
      - Real Voice: runs Speech-to-Text → continues to Support Agent
      - Text Input: bypasses audio checks, goes directly to Support Agent
      - Memory Engine: reads History, Previous Tickets, Resolutions, Sentiments, Fraud Attempts
      - LLM Reasoning: synthesizes response & analyzes customer sentiment
      - Text-to-Speech: outputs AI voice response if output preference is "voice"
    """

    def __init__(self):
        self.memory       = MemoryManager()
        self.detector     = DetectionTool()
        self.reporter     = ReportTool()
        self.risk_scorer  = RiskScorer()

    # ── Public API ────────────────────────────────────────────────────────────

    def analyze(
        self,
        audio_path: str = None,
        filename: str = None,
        context: dict = None,
        input_type: str = "voice",
        text_input: str = "",
        output_preference: str = "text"
    ) -> dict:
        """
        Runs the full Customer support agent memory & detection loop.
        """
        if context is None:
            context = {}

        # Ensure submitter is defined
        submitter = context.get("submitter", "Unknown").strip() or "Unknown"
        context["submitter"] = submitter
        department = context.get("department", "General").strip() or "General"
        context["department"] = department
        purpose = context.get("purpose", "Not specified").strip() or "Not specified"
        context["purpose"] = purpose

        # Initialize default variables
        is_fake = False
        confidence = 0.0
        detection = {
            "is_fake": False,
            "confidence": 0.0,
            "proba_cnn": 0.0,
            "proba_lstm": 0.0,
            "proba_bio": 0.0,
            "duration_sec": 0.0
        }
        transcription = text_input

        # ── 1. Input Processing ──
        if input_type == "voice" and audio_path and os.path.exists(audio_path):
            # Run Deepfake Detection
            detection = self.detector.detect(audio_path)
            is_fake = detection["is_fake"]
            confidence = detection["confidence"]

            if is_fake:
                # [VOICE INPUT: FAKE] -> Log to Fraud Memory -> Trigger Security Warning
                context["transcription"] = "[VOICE SIGNATURE FRAUD ATTEMPT - LOCKED]"
                context["sentiment"] = "NEGATIVE"
                context["input_type"] = "voice"

                # Save case to episodic memory
                case_id = self.memory.episodic.store_detection(audio_path, filename, detection, context)
                
                # Generate security warning
                warning_text = (
                    f"CRITICAL SECURITY ALERT:\n"
                    f"Voice verification failed. A cloned or synthetic voice signature (Deepfake) "
                    f"was detected with confidence {confidence * 100:.1f}%.\n"
                    f"For compliance and security, the request from customer '{submitter}' has been blocked. "
                    f"This security lock has been logged into the Fraud Memory Registry under Case ID: {case_id}."
                )

                # Generate compliance audit report
                report = self.reporter.generate(case_id, warning_text, detection, "Voice Fraud Attempt Pattern Detected", context)
                
                # Update case in database
                self.memory.episodic.update_case(
                    case_id,
                    warning_text,
                    report,
                    {"level": "CRITICAL", "score": 10.0},
                    "NEGATIVE"
                )

                # If Voice output preference, synthesize warning speech
                speech_url = None
                if output_preference == "voice":
                    speech_path = REPORTS_DIR / f"speech_{case_id}.mp3"
                    self._run_tts(warning_text, str(speech_path))
                    speech_url = f"/agent/speech/{case_id}"

                return {
                    "case_id":       case_id,
                    "filename":      filename,
                    "detection":     detection,
                    "analysis":      warning_text,
                    "risk_level":    "CRITICAL",
                    "risk_score":    10.0,
                    "patterns_found": "Voice Fraud Attempt pattern detected. This submitter is locked.",
                    "report_url":    report.get("url"),
                    "speech_url":    speech_url,
                    "timestamp":     datetime.now(timezone.utc).isoformat(),
                    "context":       context,
                    "sentiment":     "NEGATIVE",
                    "transcription": context["transcription"],
                    "input_type":    "voice",
                    "is_fraud":      True
                }
            else:
                # [VOICE INPUT: REAL] -> Speech-to-Text
                transcription = self._run_stt(audio_path)
                if not transcription or transcription.startswith("[Transcribing failed"):
                    transcription = purpose

        # ── 2. Query Memory Engine ──
        customer_profile = self.memory.get_customer_profile(submitter)
        context["transcription"] = transcription
        context["input_type"] = input_type

        # Format history context for the LLM
        history_lines = []
        for h in customer_profile["history"][-5:]:
            history_lines.append(
                f"- Ticket {h['case_id']} ({h['timestamp'][:10]}): Query: \"{h['transcription']}\" | Resolution: \"{h['resolution'][:100]}...\" | Sentiment: {h['sentiment']}"
            )
        history_str = "\n".join(history_lines) if history_lines else "No prior history on record."

        # Format sentiment timeline
        sentiment_timeline = [h["sentiment"] for h in customer_profile["history"] if h.get("sentiment")]
        sentiment_str = " ➔ ".join(sentiment_timeline) if sentiment_timeline else "None"

        # Format fraud history
        fraud_str = f"{customer_profile['fraud_attempts_count']} deepfake voice fraud attempt(s) detected previously."

        # Search Knowledge Base (policies and playbooks)
        kb_query = f"Customer support policy for {department}: {transcription}"
        regulations = self.memory.semantic.query(kb_query)

        # Search Pattern Engine (prior team interactions)
        patterns = self.memory.pattern_engine.find_patterns(
            department=department,
            time_window_days=30
        )

        # Risk Scorer
        risk = self.risk_scorer.compute(detection, patterns)

        # ── 3. LLM Reasoning ──
        analysis_raw = self._run_llm(
            transcription=transcription,
            regulations=regulations,
            patterns=patterns,
            risk=risk,
            context=context,
            history_str=history_str,
            sentiment_str=sentiment_str,
            fraud_str=fraud_str
        )

        # Extract sentiment tag and response text
        sentiment = "NEUTRAL"
        analysis_response = analysis_raw
        
        sent_match = re.search(r"<sentiment>(.*?)</sentiment>", analysis_raw, re.DOTALL | re.IGNORECASE)
        resp_match = re.search(r"<response>(.*?)</response>", analysis_raw, re.DOTALL | re.IGNORECASE)
        
        if sent_match:
            sentiment = sent_match.group(1).strip().upper()
        if resp_match:
            analysis_response = resp_match.group(1).strip()
        else:
            # Clean up tags if matches didn't capture exactly but tags exist
            analysis_response = re.sub(r"<sentiment>.*?</sentiment>", "", analysis_response, flags=re.DOTALL | re.IGNORECASE).strip()
            analysis_response = re.sub(r"<response>|</response>", "", analysis_response, flags=re.DOTALL | re.IGNORECASE).strip()

        context["sentiment"] = sentiment

        # ── 4. Episodic Memory Storage ──
        case_id = self.memory.episodic.store_detection(audio_path, filename, detection, context)

        # Generate report
        report = self.reporter.generate(case_id, analysis_response, detection, patterns, context)

        # Save updates
        self.memory.episodic.update_case(case_id, analysis_response, report, risk, sentiment)

        # ── 5. Voice Output Preference ──
        speech_url = None
        if output_preference == "voice":
            speech_path = REPORTS_DIR / f"speech_{case_id}.mp3"
            self._run_tts(analysis_response, str(speech_path))
            speech_url = f"/agent/speech/{case_id}"

        # Re-fetch customer profile with this interaction included
        updated_profile = self.memory.get_customer_profile(submitter)

        return {
            "case_id":         case_id,
            "filename":        filename,
            "detection":       detection,
            "analysis":        analysis_response,
            "risk_level":      risk["level"],
            "risk_score":      risk["score"],
            "patterns_found":   patterns,
            "report_url":      report.get("url"),
            "speech_url":      speech_url,
            "timestamp":       datetime.now(timezone.utc).isoformat(),
            "context":         context,
            "sentiment":       sentiment,
            "transcription":   transcription,
            "input_type":      input_type,
            "customer_profile": updated_profile,
            "is_fraud":        False
        }

    # ── Private helpers ───────────────────────────────────────────────────────

    def _run_stt(self, audio_path: str) -> str:
        """Transcribe audio using OpenAI Whisper API. Falls back to mock transcript if unavailable."""
        if _HAS_OPENAI and _openai_client:
            try:
                with open(audio_path, "rb") as fh:
                    transcript = _openai_client.audio.transcriptions.create(
                        model="whisper-1",
                        file=fh
                    )
                return transcript.text.strip()
            except Exception as e:
                return f"[Transcribing failed: {e}]"
        return "This is a fallback transcript because the OpenAI API Key is not configured."

    def _run_tts(self, text: str, output_path: str):
        """Synthesize speech using OpenAI Text-to-Speech API."""
        if _HAS_OPENAI and _openai_client:
            try:
                # Strip markdown for speech synthesis
                clean_text = re.sub(r"[*#_`\-]", "", text)[:1000]
                response = _openai_client.audio.speech.create(
                    model="tts-1",
                    voice="alloy",
                    input=clean_text
                )
                response.stream_to_file(output_path)
            except Exception as e:
                print(f"TTS generation failed: {e}")

    def _run_llm(
        self,
        transcription: str,
        regulations:   str,
        patterns:      str,
        risk:          dict,
        context:       dict,
        history_str:   str,
        sentiment_str: str,
        fraud_str:     str,
    ) -> str:
        """Call OpenAI GPT-4o with full context. Falls back to structured stub if unavailable."""

        user_message = f"""
USER INPUT / TICKET TRANSCRIPT:
"{transcription}"

CUSTOMER MEMORY ENGINE PROFILE:
  Customer: {context.get("submitter", "Unknown")}
  Previous Tickets & History:
  {history_str}
  
  Sentiment Timeline (oldest to newest):
  {sentiment_str}
  
  Prior Voice Fraud Attempts:
  {fraud_str}

KNOWLEDGE BASE regulations & resolutions:
{regulations}

PRIOR PATTERNS (department):
{patterns}

COMPOSITE RISK: Score {risk["score"]}/10 | Level: {risk["level"]}

TASK:
1. Determine the customer's sentiment for the current query. Choose exactly one value: POSITIVE, NEUTRAL, or NEGATIVE.
2. Generate a helpful, memory-aware resolution response. Lead with memory context — do not ask the customer to re-explain prior tickets. Reference their history and build trust.

FORMAT YOUR RESPONSE EXACTLY LIKE THIS:
<sentiment>YOUR_SENTIMENT_HERE</sentiment>
<response>
Provide a full support agent response using the VoiceGuard guidelines:
- Include a situation summary acknowledging their history
- Incorporate memory context from their previous tickets
- Note pattern assessments
- Recommend 3 specific actions
- Mention long-term improvements
</response>
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
                return self._fallback_analysis(transcription, patterns, risk, context, history_str, error=str(e))

        return self._fallback_analysis(transcription, patterns, risk, context, history_str)

    @staticmethod
    def _fallback_analysis(
        transcription: str,
        patterns:  str,
        risk:      dict,
        context:   dict,
        history_str: str,
        error:     str = "",
    ) -> str:
        """
        Structured fallback when OpenAI is unavailable.
        Produces deterministic, rule-based analysis with sentiment detection.
        """
        customer  = context.get("submitter", "Unknown")
        dept      = context.get("department", "Unknown")
        note      = f"\n[Note: LLM unavailable — rule-based agent response. {error}]" if error else ""

        # Determine a mock sentiment from transcription keywords
        text_lower = transcription.lower()
        if any(w in text_lower for w in ["fail", "error", "broken", "bad", "wrong", "delay", "fraud", "scam"]):
            sentiment = "NEGATIVE"
        elif any(w in text_lower for w in ["thank", "great", "good", "perfect", "resolved", "awesome"]):
            sentiment = "POSITIVE"
        else:
            sentiment = "NEUTRAL"

        response_body = f"""1. SITUATION SUMMARY
{customer} ({dept}) submitted: "{transcription}". Memory shows prior ticket context. Handled using standard compliance resolution rules.{note}

2. MEMORY CONTEXT
{history_str}

3. PATTERN ASSESSMENT
{patterns}

4. RECOMMENDED ACTIONS (next 24 hours)
1. Assign request to the primary handler for {dept}.
2. Review history for {customer} before reaching out.
3. Inform the client that prior ticket resolutions have been loaded for context.

5. LONG-TERM IMPROVEMENTS
• Keep monitoring sentiment for {customer} which is currently {sentiment}."""

        return f"<sentiment>{sentiment}</sentiment>\n<response>\n{response_body}\n</response>"

