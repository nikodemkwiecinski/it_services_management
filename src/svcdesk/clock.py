# ai-generated: 90% - Claude Code drafted, reviewed by me
"""Per-request "now" (API.md section 8) and RFC 3339 formatting (R-17)."""

import os
import re
from datetime import datetime, timezone

HEADER = "X-Test-Clock"

# Date, time with seconds, optional fraction, mandatory offset: a naive timestamp is malformed.
_RFC3339 = re.compile(
    r"^\d{4}-\d{2}-\d{2}[Tt ]\d{2}:\d{2}:\d{2}(\.\d+)?([Zz]|[+-]\d{2}:\d{2})$"
)


class InvalidClock(ValueError):
    pass


def test_clock_enabled() -> bool:
    return os.environ.get("SVCDESK_TEST_CLOCK", "").strip().lower() in ("1", "true")


def parse_instant(value: str) -> datetime:
    """Parse an RFC 3339 instant with an offset into an aware UTC datetime."""
    value = value.strip()
    if not _RFC3339.match(value):
        raise InvalidClock(f"not an RFC 3339 instant with an offset: {value!r}")
    normalised = value.upper().replace(" ", "T")
    if normalised.endswith("Z"):
        normalised = normalised[:-1] + "+00:00"
    try:
        parsed = datetime.fromisoformat(normalised)
    except ValueError as exc:
        raise InvalidClock(str(exc)) from exc
    return parsed.astimezone(timezone.utc)


def request_now(header_value: str | None) -> datetime:
    """The request's "now": the test clock header when enabled and present, else real UTC time."""
    if header_value is not None and test_clock_enabled():
        return parse_instant(header_value)
    return datetime.now(timezone.utc)


def format_instant(value: datetime | None) -> str | None:
    """UTC with a Z suffix; fractional seconds only when present."""
    if value is None:
        return None
    value = value.astimezone(timezone.utc)
    text = value.strftime("%Y-%m-%dT%H:%M:%S")
    if value.microsecond:
        text += f".{value.microsecond:06d}"
    return text + "Z"
