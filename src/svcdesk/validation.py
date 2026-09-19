# ai-generated: 90% - Claude Code drafted, reviewed by me
"""Create-ticket validation (R-03, R-20, API.md section 7) on the raw JSON body."""

from typing import Any


class ValidationError(ValueError):
    pass


def _is_int(value: Any) -> bool:
    # bool is a subclass of int in Python; `true` is not an impact level.
    return isinstance(value, int) and not isinstance(value, bool)


def _string(value: Any, field: str, minimum: int, maximum: int) -> str:
    if not isinstance(value, str):
        raise ValidationError(f"{field} must be a string")
    if not minimum <= len(value) <= maximum:
        raise ValidationError(f"{field} must be {minimum} to {maximum} characters")
    return value


def _level(body: dict, field: str) -> int:
    if field not in body or body[field] is None:
        raise ValidationError(f"{field} is required")
    value = body[field]
    if not _is_int(value) or not 1 <= value <= 3:
        raise ValidationError(f"{field} must be an integer from 1 to 3")
    return value


def validate_create(body: Any) -> dict:
    """Return the client-owned fields of a new ticket; server-owned and unknown fields are dropped."""
    if not isinstance(body, dict):
        raise ValidationError("request body must be a JSON object")

    if body.get("title") is None:
        raise ValidationError("title is required")
    title = _string(body["title"], "title", 1, 200)

    description = body.get("description")
    description = "" if description is None else _string(description, "description", 0, 4000)

    reporter = body.get("reporter")
    if not isinstance(reporter, dict):
        raise ValidationError("reporter is required and must be an object")
    if reporter.get("name") is None:
        raise ValidationError("reporter.name is required")
    name = _string(reporter["name"], "reporter.name", 1, 100)
    email = reporter.get("email")
    if email is not None and not isinstance(email, str):
        raise ValidationError("reporter.email must be a string or null")
    vip = reporter.get("vip")
    if vip is None:
        vip = False
    elif not isinstance(vip, bool):
        raise ValidationError("reporter.vip must be a boolean")

    impact = _level(body, "impact")
    urgency = _level(body, "urgency")

    related_to = body.get("related_to")
    if related_to is not None and not isinstance(related_to, str):
        raise ValidationError("related_to must be a ticket id or null")

    return {
        "title": title,
        "description": description,
        "reporter": {"name": name, "email": email, "vip": vip},
        "impact": impact,
        "urgency": urgency,
        "related_to": related_to,
    }
