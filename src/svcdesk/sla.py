# ai-generated: 90% - Claude Code drafted, I checked it against the vectors T1..T8
"""SLA due instants, breach and pause (R-12..R-16, API.md sections 4 and 5) and decision C1."""

from datetime import datetime, time, timedelta, timezone
from zoneinfo import ZoneInfo

from . import decisions

WARSAW = ZoneInfo("Europe/Warsaw")
OPEN = time(8, 0)
CLOSE = time(16, 0)

TARGETS = {  # priority: (acknowledge within, resolve within)
    "P1": (timedelta(minutes=15), timedelta(hours=4)),
    "P2": (timedelta(hours=1), timedelta(hours=8)),
    "P3": (timedelta(hours=4), timedelta(hours=24)),
    "P4": (timedelta(hours=8), timedelta(hours=72)),
}


def uses_business_clock(priority: str) -> bool:
    return not (priority == "P1" and decisions.C1 == "wallclock")


def is_business_time(moment: datetime) -> bool:
    local = moment.astimezone(WARSAW)
    return local.weekday() < 5 and OPEN <= local.time() < CLOSE


def _next_opening(local: datetime) -> datetime:
    """Move a naive local time forward into a business window (unchanged if already inside one)."""
    while True:
        if local.weekday() >= 5 or local.time() >= CLOSE:
            local = datetime.combine(local.date() + timedelta(days=1), OPEN)
        elif local.time() < OPEN:
            local = datetime.combine(local.date(), OPEN)
        else:
            return local


def add_business_time(start: datetime, target: timedelta) -> datetime:
    """Consume `target` from consecutive business windows starting at `start` (aware); return UTC.

    Works in naive Europe/Warsaw wall time: DST changes happen on Sunday nights, never inside a window.
    A target that ends exactly at closing time is due at 16:00 that day (the tie rule).
    """
    local = start.astimezone(WARSAW).replace(tzinfo=None)
    remaining = target
    while True:
        local = _next_opening(local)
        closing = datetime.combine(local.date(), CLOSE)
        available = closing - local
        if remaining <= available:
            return (local + remaining).replace(tzinfo=WARSAW).astimezone(timezone.utc)
        remaining -= available
        local = closing


def due_instants(priority: str, created_at: datetime) -> tuple[datetime, datetime]:
    ack_target, resolve_target = TARGETS[priority]
    if uses_business_clock(priority):
        return add_business_time(created_at, ack_target), add_business_time(created_at, resolve_target)
    return created_at + ack_target, created_at + resolve_target


def status(
    *,
    priority: str,
    state: str,
    ack_due_at: datetime,
    resolve_due_at: datetime,
    acknowledged_at: datetime | None,
    resolved_at: datetime | None,
    now: datetime,
) -> dict:
    """Breach and pause at `now`; reaching a due instant exactly is not a breach."""
    if acknowledged_at is None:
        ack_breached = now > ack_due_at
    else:
        ack_breached = acknowledged_at > ack_due_at
    if resolved_at is None:
        resolve_breached = now > resolve_due_at
    else:
        resolve_breached = resolved_at > resolve_due_at
    paused = (
        state not in ("resolved", "closed")
        and uses_business_clock(priority)
        and not is_business_time(now)
    )
    return {"ack_breached": ack_breached, "resolve_breached": resolve_breached, "paused": paused}
