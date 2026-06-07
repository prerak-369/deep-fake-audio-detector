"""
Memory manager — unified interface to all three memory layers.
Instantiated once by ComplianceAgent and shared across the analysis pipeline.
"""

from agent.memory.episodic       import EpisodicMemory
from agent.memory.semantic       import SemanticMemory
from agent.memory.pattern_engine import PatternEngine


class MemoryManager:
    def __init__(self):
        self.episodic       = EpisodicMemory()
        self.semantic       = SemanticMemory()
        self.pattern_engine = PatternEngine(self.episodic)

    def get_customer_profile(self, submitter: str, days: int = 30) -> dict:
        """
        Compile complete customer relationship memory:
          - History of previous tickets & inputs
          - Past resolutions
          - Sentiment timeline
          - Audio deepfake fraud attempts history
        """
        if not submitter or submitter.lower() == "unknown":
            return {
                "submitter": "Unknown",
                "history": [],
                "sentiment_timeline": [],
                "fraud_attempts_count": 0,
                "fraud_attempts_detail": []
            }
        recent = self.episodic.get_recent_by_submitter(submitter, days)
        # Reverse to get oldest-to-newest chronological order for timeline
        chrono_recent = list(reversed(recent))
        
        history = []
        sentiment_timeline = []
        fraud_attempts = []
        
        for case in chrono_recent:
            history.append({
                "case_id": case["case_id"],
                "timestamp": case["timestamp"],
                "purpose": case["purpose"] or "No summary",
                "transcription": case["transcription"] or case["purpose"] or "",
                "resolution": case["analysis_text"] or "Pending",
                "is_fake": case["is_fake"],
                "sentiment": case["sentiment"] or "NEUTRAL"
            })
            sentiment_timeline.append({
                "case_id": case["case_id"],
                "timestamp": case["timestamp"],
                "sentiment": case["sentiment"] or "NEUTRAL"
            })
            if case["is_fake"]:
                fraud_attempts.append({
                    "case_id": case["case_id"],
                    "timestamp": case["timestamp"],
                    "confidence": case["confidence"]
                })
        
        return {
            "submitter": submitter,
            "history": history,
            "sentiment_timeline": sentiment_timeline,
            "fraud_attempts_count": len(fraud_attempts),
            "fraud_attempts_detail": fraud_attempts
        }

