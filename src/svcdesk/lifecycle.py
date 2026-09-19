# ai-generated: 90% - Claude Code drafted, reviewed by me
"""State machine and reopen window (R-07..R-11, API.md section 6) and decision C2."""

from datetime import datetime, timedelta

from . import decisions
from .clock import format_instant, parse_instant

REOPEN_WINDOW = timedelta(days=7)

# action: (required state, new state, timestamp field set to now)
TRANSITIONS = {
    "ack": ("new", "acknowledged", "acknowledged_at"),
    "start": ("acknowledged", "in_progress", None),
    "resolve": ("in_progress", "resolved", "resolved_at"),
    "close": ("resolved", "closed", "closed_at"),
}


class TransitionRefused(Exception):
    def __init__(self, code: str, message: str) -> None:
        super().__init__(message)
        self.code = code
        self.message = message


def _within_window(stamp: str | None, now: datetime) -> bool:
    # The request clock is compared only with the event it reopens; an earlier clock is not an error.
    return stamp is not None and now <= parse_instant(stamp) + REOPEN_WINDOW


def apply(ticket: dict, action: str, now: datetime) -> dict:
    """Return the ticket after `action`, or raise TransitionRefused (answered with 409)."""
    state = ticket["state"]
    if action == "reopen":
        if state == "resolved":
            if not _within_window(ticket.get("resolved_at"), now):
                raise TransitionRefused("reopen_window_expired", "the 7-day reopen window has passed")
        elif state == "closed":
            if decisions.C2 == "immutable":
                raise TransitionRefused(
                    "ticket_closed",
                    "a closed ticket is immutable; create a new ticket with related_to",
                )
            if not _within_window(ticket.get("closed_at"), now):
                raise TransitionRefused("reopen_window_expired", "the 7-day reopen window has passed")
        else:
            raise TransitionRefused("invalid_transition", f"cannot reopen a ticket in state {state}")
        ticket["state"] = "in_progress"
        ticket["resolved_at"] = None
        ticket["closed_at"] = None
        return ticket

    required, target, stamp_field = TRANSITIONS[action]
    if state != required:
        raise TransitionRefused("invalid_transition", f"cannot {action} a ticket in state {state}")
    ticket["state"] = target
    if stamp_field:
        ticket[stamp_field] = format_instant(now)
    return ticket
