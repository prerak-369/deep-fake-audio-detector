"""
Pattern engine — detects coordinated attack campaigns and repeat targeting
by analysing episodic memory for temporal clustering within a department.
"""

from agent.memory.episodic import EpisodicMemory


class PatternEngine:
    def __init__(self, episodic: EpisodicMemory):
        self.episodic = episodic

    def find_patterns(self, department: str | None, time_window_days: int = 30) -> str:
        """
        Query recent episodic history for the given department and detect patterns.
        Returns a human-readable string consumed by the agent's prompt.
        """
        if not department:
            return "No department specified — cross-department pattern analysis skipped."

        recent     = self.episodic.get_recent_by_department(department, time_window_days)
        all_cases  = recent                                 # total submissions
        fake_cases = [c for c in recent if c.get("is_fake")]
        total      = len(all_cases)
        fakes      = len(fake_cases)

        if fakes == 0:
            return (
                f"No deepfake incidents detected in the {department} department "
                f"over the last {time_window_days} days "
                f"({total} total submission{'s' if total != 1 else ''} reviewed)."
            )

        timestamps = [c.get("timestamp", "unknown")[:19].replace("T", " ") for c in fake_cases]
        submitters = sorted({c.get("submitter", "Unknown") for c in fake_cases})

        lines = [
            f"PATTERN ALERT — {fakes} deepfake incident(s) targeting the "
            f"{department} department in the last {time_window_days} days.",
            f"  Incident timestamps : {', '.join(timestamps)}",
            f"  Unique submitter(s) : {', '.join(submitters)}",
            f"  Total submissions   : {total} ({fakes} flagged as fake)",
        ]

        if fakes >= 3:
            lines.append(
                "\nTHREAT ASSESSMENT ▶ HIGH — Frequency and concentration strongly "
                "suggest a coordinated fraud campaign targeting this department. "
                "Immediate escalation to Legal and Information Security is recommended."
            )
        elif fakes == 2:
            lines.append(
                "\nTHREAT ASSESSMENT ▶ MEDIUM — Repeat targeting detected. "
                "Enhanced verification protocols should be activated for all "
                f"{department} department audio authorisations."
            )
        else:
            lines.append(
                "\nTHREAT ASSESSMENT ▶ LOW — Single prior incident. "
                "Monitor closely and ensure the submitter account has not been compromised."
            )

        return "\n".join(lines)
