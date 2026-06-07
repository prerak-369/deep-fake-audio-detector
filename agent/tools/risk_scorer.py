"""
Risk scorer — computes a composite 0–10 risk score from detection result + pattern history.
No external dependencies.
"""


class RiskScorer:
    """
    Score breakdown:
      Detection component (max 5 pts): confidence × 5 if fake, 0 if authentic
      Pattern component   (max 5 pts): severity of historical pattern
        - Coordinated campaign (3+ incidents) → 5.0
        - Repeat targeting (2 incidents)      → 3.0
        - Single prior incident               → 1.5
        - No prior incidents                  → 0.0

    Risk levels:
      CRITICAL  ≥ 8.0
      HIGH      ≥ 6.0
      MEDIUM    ≥ 3.0
      LOW       < 3.0
    """

    def compute(self, detection: dict, patterns: str) -> dict:
        score = 0.0

        # ── Detection contribution ────────────────────────────────────────────
        if detection.get("is_fake"):
            score += detection.get("confidence", 0.5) * 5.0

        # ── Pattern contribution (repeat tickets / escalation history) ────────
        if patterns and "PATTERN ALERT" in patterns:
            if "PRIORITY ASSESSMENT ▶ HIGH" in patterns:
                score += 5.0
            elif "PRIORITY ASSESSMENT ▶ MEDIUM" in patterns:
                score += 3.0
            else:
                score += 1.5

        score = min(round(score, 1), 10.0)

        if score >= 8.0:
            level = "CRITICAL"
        elif score >= 6.0:
            level = "HIGH"
        elif score >= 3.0:
            level = "MEDIUM"
        else:
            level = "LOW"

        return {"score": score, "level": level}
