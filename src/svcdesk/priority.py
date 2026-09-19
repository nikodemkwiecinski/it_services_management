# ai-generated: 90% - Claude Code drafted, reviewed by me
"""Priority from the impact/urgency matrix (R-04, R-05) and decision C3 (API.md section 3)."""

from . import decisions

# MATRIX[impact][urgency]
MATRIX = {
    1: {1: "P1", 2: "P2", 3: "P3"},
    2: {1: "P2", 2: "P3", 3: "P4"},
    3: {1: "P3", 2: "P4", 3: "P4"},
}


def compute_priority(impact: int, urgency: int, vip: bool) -> str:
    priority = MATRIX[impact][urgency]
    if decisions.C3 == "vip" and vip and priority in ("P3", "P4"):
        priority = "P2"
    return priority
