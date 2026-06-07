"""
Pattern engine — detects repeat support tickets and escalating interaction
patterns by analysing episodic memory within a department or team.
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
            return "No department specified — cross-team interaction history skipped."

        recent      = self.episodic.get_recent_by_department(department, time_window_days)
        total       = len(recent)
        escalated   = [c for c in recent if c.get("is_fake")]
        submitters  = sorted({c.get("submitter", "Unknown") for c in recent})

        if total == 0:
            return (
                f"No prior support tickets on record for {department} "
                f"in the last {time_window_days} days — this appears to be a first contact."
            )

        if total == 1:
            return (
                f"One prior interaction for {department} in the last {time_window_days} days. "
                f"No repeat-ticket pattern yet — treat as isolated unless context suggests otherwise."
            )

        timestamps = [c.get("timestamp", "unknown")[:19].replace("T", " ") for c in recent]
        purposes   = [c.get("purpose", "")[:50] for c in recent if c.get("purpose")]

        lines = [
            f"PATTERN ALERT — {total} prior support ticket(s) for "
            f"{department} in the last {time_window_days} days.",
            f"  Interaction timestamps : {', '.join(timestamps[:5])}{'…' if total > 5 else ''}",
            f"  Customer(s) involved   : {', '.join(submitters)}",
            f"  Escalated tickets      : {len(escalated)} of {total} marked high-priority",
        ]
        if purposes:
            lines.append(f"  Related issue themes   : {'; '.join(purposes[:3])}")

        if total >= 3:
            lines.append(
                "\nPRIORITY ASSESSMENT ▶ HIGH — Repeat contact pattern detected. "
                "Customer should not need to re-explain. Pull full history, assign a "
                "dedicated owner, and apply known-issue resolution playbook immediately."
            )
        else:
            lines.append(
                "\nPRIORITY ASSESSMENT ▶ MEDIUM — Repeat ticket detected. "
                "Reference prior interactions explicitly in the response and verify "
                f"whether the root cause for {department} was fully resolved."
            )

        return "\n".join(lines)
