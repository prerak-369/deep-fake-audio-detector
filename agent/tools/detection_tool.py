"""
Detection tool — thin wrapper around the existing Predictor singleton.
Calls predict() directly (in-process) instead of HTTP to avoid round-trip latency.
"""

import sys
from pathlib import Path

ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(ROOT))

from api.predictor import get_predictor


class DetectionTool:
    """Wraps the CNN/LSTM/Bio-MLP ensemble for use by the compliance agent."""

    def detect(self, audio_path: str) -> dict:
        """
        Run inference on an audio file.

        Returns:
            is_fake    (bool)  — True if the ensemble classifies as fake
            confidence (float) — probability of being fake (0.0–1.0)
            proba_cnn  (float) — CNN sub-model score
            proba_lstm (float) — LSTM sub-model score
            proba_bio  (float) — Biometrics MLP sub-model score
            duration_sec (float)
        """
        predictor = get_predictor()
        raw = predictor.predict(audio_path)
        return {
            "is_fake":      raw["verdict"] == "FAKE",
            "confidence":   raw["confidence"],
            "proba_cnn":    raw["proba_cnn"],
            "proba_lstm":   raw["proba_lstm"],
            "proba_bio":    raw["proba_bio"],
            "duration_sec": raw["duration_sec"],
        }
