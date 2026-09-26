# ai-generated: 90% - Claude Code drafted from lab2/METRIC-SPEC.md, reviewed by me
"""DORA delivery metrics over an event log (lab2/METRIC-SPEC.md sections 1-6, rules R-01..R-17)."""

from datetime import datetime, timedelta
from decimal import ROUND_HALF_UP, Decimal
from typing import Any

from .clock import InvalidClock, format_instant, parse_instant
from .validation import ValidationError

SPEC_VERSION = "1.0.0"

EVENT_TYPES = ("commit", "deployment", "incident")
OUTCOMES = ("success", "failure")
PHASES = ("opened", "resolved")


# --- parsing and well-formedness (section 1) -------------------------------------------------------------


def _instant(value: Any, field: str) -> datetime:
    if not isinstance(value, str):
        raise ValidationError(f"{field} must be an RFC 3339 instant")
    try:
        return parse_instant(value)
    except InvalidClock as exc:
        raise ValidationError(f"{field}: {exc}") from exc


def _text(event: dict, field: str, where: str, nullable: bool = False) -> str | None:
    value = event.get(field)
    if value is None and nullable:
        return None
    if not isinstance(value, str) or not value:
        raise ValidationError(f"{where}: {field} must be a non-empty string" + (" or null" if nullable else ""))
    return value


def _names(event: dict, field: str, where: str) -> list[str]:
    value = event.get(field)
    if not isinstance(value, list) or not all(isinstance(item, str) and item for item in value):
        raise ValidationError(f"{where}: {field} must be an array of strings")
    # A name listed twice in one event is one reference.
    return list(dict.fromkeys(value))


def parse_window(body: Any) -> tuple[datetime, datetime]:
    if not isinstance(body, dict):
        raise ValidationError("request body must be a JSON object")
    window = body.get("window")
    if not isinstance(window, dict):
        raise ValidationError("window is required and must be an object")
    start = _instant(window.get("from"), "window.from")
    end = _instant(window.get("to"), "window.to")
    if end <= start:
        raise ValidationError("window.to must be after window.from")
    return start, end


def parse_events(body: dict) -> dict:
    """Deduplicate (R-05), parse every event and check that the log is well formed."""
    events = body.get("events")
    if not isinstance(events, list):
        raise ValidationError("events is required and must be an array")

    commits: dict[str, dict] = {}
    deployments: list[dict] = []
    incidents: dict[str, dict] = {}
    seen: set[str] = set()

    for index, event in enumerate(events):
        where = f"events[{index}]"
        if not isinstance(event, dict):
            raise ValidationError(f"{where} must be an object")
        event_id = event.get("event_id")
        if not isinstance(event_id, str) or not 1 <= len(event_id) <= 64:
            raise ValidationError(f"{where}: event_id must be a string of 1 to 64 characters")
        if event_id in seen:
            continue  # R-05: the first occurrence wins
        seen.add(event_id)
        where = f"event {event_id}"

        kind = event.get("type")
        if kind not in EVENT_TYPES:
            raise ValidationError(f"{where}: type must be one of {', '.join(EVENT_TYPES)}")
        at = _instant(event.get("at"), f"{where}: at")

        if kind == "commit":
            sha = _text(event, "sha", where)
            _text(event, "branch", where)
            change_id = _text(event, "change_id", where, nullable=True)
            reverts = _text(event, "reverts", where, nullable=True)
            if sha in commits:
                raise ValidationError(f"{where}: sha {sha} is not unique")
            if (change_id is None) == (reverts is None):
                raise ValidationError(f"{where}: a commit carries a change_id exactly when reverts is null")
            commits[sha] = {"sha": sha, "at": at, "branch": event["branch"], "change_id": change_id,
                            "reverts": reverts}

        elif kind == "deployment":
            outcome = event.get("outcome")
            if outcome not in OUTCOMES:
                raise ValidationError(f"{where}: outcome must be success or failure")
            if not isinstance(event.get("unplanned"), bool):
                raise ValidationError(f"{where}: unplanned must be a boolean")
            deployments.append({
                "deployment_id": _text(event, "deployment_id", where),
                "at": at,
                "environment": _text(event, "environment", where),
                "outcome": outcome,
                "commits": _names(event, "commits", where),
                "unplanned": event["unplanned"],
                "caused_by": _text(event, "caused_by", where, nullable=True),
            })

        else:
            incident_id = _text(event, "incident_id", where)
            phase = event.get("phase")
            if phase not in PHASES:
                raise ValidationError(f"{where}: phase must be opened or resolved")
            incident = incidents.setdefault(incident_id, {"incident_id": incident_id, "opened": None,
                                                          "resolved": None, "deployments": set()})
            if incident[phase] is not None:
                raise ValidationError(f"{where}: incident {incident_id} is {phase} more than once")
            incident[phase] = at
            incident["deployments"].update(_names(event, "deployments", where))

    deployment_ids = {deployment["deployment_id"] for deployment in deployments}
    for commit in commits.values():
        if commit["reverts"] is not None and commit["reverts"] not in commits:
            raise ValidationError(f"commit {commit['sha']} reverts {commit['reverts']}, which is not in the log")
    for deployment in deployments:
        for sha in deployment["commits"]:
            if sha not in commits:
                raise ValidationError(f"deployment {deployment['deployment_id']} carries {sha}, which is not in the log")
        if deployment["caused_by"] is not None and deployment["caused_by"] not in incidents:
            raise ValidationError(
                f"deployment {deployment['deployment_id']} is caused_by {deployment['caused_by']}, "
                "which is not in the log"
            )
    for incident in incidents.values():
        if incident["opened"] is None:
            raise ValidationError(f"incident {incident['incident_id']} resolved but was never opened")
        for deployment_id in incident["deployments"]:
            if deployment_id not in deployment_ids:
                raise ValidationError(
                    f"incident {incident['incident_id']} covers {deployment_id}, which is not in the log"
                )

    return {"commits": commits, "deployments": deployments, "incidents": incidents}


# --- arithmetic (R-03, R-04) -----------------------------------------------------------------------------


def _seconds(delta: timedelta) -> Decimal:
    return Decimal(delta.days * 86400 + delta.seconds) + Decimal(delta.microseconds) / Decimal(1_000_000)


def _whole_seconds(value: Decimal | None) -> int | None:
    return None if value is None else int(value.quantize(Decimal(1), rounding=ROUND_HALF_UP))


def _ratio(numerator: int | Decimal, denominator: int | Decimal) -> float | None:
    if not denominator:
        return None
    return float((Decimal(numerator) / Decimal(denominator)).quantize(Decimal("0.000001"), rounding=ROUND_HALF_UP))


def _median(values: list[Decimal]) -> Decimal | None:
    if not values:
        return None
    ordered = sorted(values)
    middle = len(ordered) // 2
    if len(ordered) % 2:
        return ordered[middle]
    return (ordered[middle - 1] + ordered[middle]) / 2


# --- change identity (R-06, R-07) ------------------------------------------------------------------------


def _change_of(commits: dict[str, dict]) -> dict[str, str]:
    """Map every sha to its change, following reverts transitively (R-06)."""
    change_of: dict[str, str] = {}
    for sha in commits:
        chain = []
        current = sha
        while current not in change_of and commits[current]["change_id"] is None:
            if current in chain:
                raise ValidationError(f"commit {sha} is part of a revert cycle and resolves to no change")
            chain.append(current)
            current = commits[current]["reverts"]
        change = change_of.get(current) or commits[current]["change_id"]
        for link in chain + [current]:
            change_of[link] = change
    return change_of


# --- GET /dora/ticket-events (section 7) -----------------------------------------------------------------

TICKET_PHASES = (("created", "created_at", "new"), ("acknowledged", "acknowledged_at", "acknowledged"),
                 ("resolved", "resolved_at", "resolved"), ("closed", "closed_at", "closed"))


def ticket_events(tickets: list[dict]) -> list[dict]:
    """One event per lifecycle instant a ticket holds, ordered by (at as an instant, ticket_id)."""
    # Sorting the strings would misplace fractional seconds ("...00.5Z" < "...00Z"), so compare instants;
    # two phases of one ticket at the same instant keep their life-cycle order.
    events = sorted(
        (parse_instant(ticket[field]), ticket["id"], order,
         {"ticket_id": ticket["id"], "at": ticket[field], "phase": phase, "priority": ticket["priority"],
          "state": state})
        for ticket in tickets
        for order, (phase, field, state) in enumerate(TICKET_PHASES)
        if ticket.get(field)
    )
    return [event for *_, event in events]


# --- the metrics (sections 4-6) --------------------------------------------------------------------------


def compute(body: Any) -> dict:
    """The full response of POST /dora/metrics for a request body; raises ValidationError when rejected."""
    start, end = parse_window(body)
    log = parse_events(body)
    commits, incidents = log["commits"], log["incidents"]
    change_of = _change_of(commits)

    # R-01, R-02: production deployments in [from, to), in a stable order (R-05 makes input order irrelevant).
    in_window = sorted(
        (d for d in log["deployments"] if d["environment"] == "production" and start <= d["at"] < end),
        key=lambda d: (d["at"], d["deployment_id"]),
    )
    successful = [d for d in in_window if d["outcome"] == "success"]
    failed = [d for d in in_window if d["outcome"] == "failure"]

    # R-08..R-10: one pair per sha at its first successful deployment; the branch is never consulted.
    lead_times: list[Decimal] = []
    negative_pairs = 0
    paired: set[str] = set()
    for deployment in successful:
        for sha in deployment["commits"]:
            if sha in paired:
                continue
            paired.add(sha)
            lead = _seconds(deployment["at"] - commits[sha]["at"])
            if lead < 0:
                negative_pairs += 1  # E1: clamped and counted, never discarded
                lead = Decimal(0)
            lead_times.append(lead)
    off_main = {
        sha for deployment in in_window for sha in deployment["commits"] if commits[sha]["branch"] != "main"
    }
    without_commits = sum(1 for deployment in in_window if not deployment["commits"])

    # R-12, R-13: recovery per failed deployment, from its covering incident.
    recoveries: list[Decimal] = []
    open_failures = 0
    for deployment in failed:
        covering = min(
            (i for i in incidents.values() if deployment["deployment_id"] in i["deployments"]),
            key=lambda i: (i["opened"], i["incident_id"]),
            default=None,
        )
        if covering is None or covering["resolved"] is None:
            open_failures += 1  # E5: not invented, still counted by R-14
            continue
        recoveries.append(max(_seconds(covering["resolved"] - deployment["at"]), Decimal(0)))

    intervals = sorted(
        (i["incident_id"], i["opened"], i["resolved"] if i["resolved"] is not None else end)
        for i in incidents.values()
    )
    overlapping = sum(
        1
        for index, (_, a_opened, a_end) in enumerate(intervals)
        for _, b_opened, b_end in intervals[index + 1:]
        if a_opened < b_end and b_opened < a_end
    )

    rework = sum(1 for d in in_window if d["unplanned"] and d["caused_by"] is not None)

    # R-16, R-17: changes delivered by a successful deployment in the window, from their first commit.
    first_commit: dict[str, datetime] = {}
    for sha, commit in commits.items():
        change = change_of[sha]
        if change not in first_commit or commit["at"] < first_commit[change]:
            first_commit[change] = commit["at"]
    first_delivery: dict[str, datetime] = {}
    for deployment in successful:
        for sha in deployment["commits"]:
            first_delivery.setdefault(change_of[sha], deployment["at"])
    true_lead_times = [
        max(_seconds(delivered - first_commit[change]), Decimal(0)) for change, delivered in first_delivery.items()
    ]

    days = _seconds(end - start) / Decimal(86400)
    return {
        "spec_version": SPEC_VERSION,
        "window": {"from": format_instant(start), "to": format_instant(end)},
        "deployment_frequency_per_day": _ratio(len(in_window), days) or 0.0,
        "change_lead_time_seconds_p50": _whole_seconds(_median(lead_times)),
        "failed_deployment_recovery_time_seconds_p50": _whole_seconds(_median(recoveries)),
        "change_fail_rate": _ratio(len(failed), len(in_window)),
        "deployment_rework_rate": _ratio(rework, len(in_window)),
        "counts": {
            "deployments": len(in_window),
            "successful_deployments": len(successful),
            "failed_deployments": len(failed),
            "recovered_failures": len(recoveries),
            "open_failures": open_failures,
            "rework_deployments": rework,
            "lead_time_pairs": len(lead_times),
            "changes": len(set(change_of.values())),
        },
        "anomalies": {
            "negative_lead_time_pairs": negative_pairs,
            "deployments_without_commits": without_commits,
            "commits_never_on_main": len(off_main),
            "revert_chains_collapsed": sum(1 for commit in commits.values() if commit["reverts"] is not None),
            "overlapping_incident_pairs": overlapping,
        },
        "ground_truth": {
            "changes_delivered": len(first_delivery),
            "true_change_lead_time_seconds_p50": _whole_seconds(_median(true_lead_times)),
        },
    }
