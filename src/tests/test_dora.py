# ai-generated: 90% - Claude Code drafted, reviewed by me
"""Tests for the Lab 2 DORA endpoints: the engine directly, and the running service over HTTP."""

import json
import os
import urllib.error
import urllib.request
from decimal import Decimal

import pytest

from svcdesk import dora
from svcdesk.validation import ValidationError

URL = os.environ.get("SVCDESK_URL", "http://localhost:8080")
FIXTURES = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "fixtures")
WINDOW = {"from": "2026-09-01T00:00:00Z", "to": "2026-09-22T00:00:00Z"}


def practice_log() -> list[dict]:
    with open(os.path.join(FIXTURES, "events-practice.jsonl"), encoding="utf-8") as handle:
        return [json.loads(line) for line in handle if line.strip()]


def practice_expected() -> dict:
    with open(os.path.join(FIXTURES, "metrics-practice.json"), encoding="utf-8") as handle:
        return json.load(handle)


def call(method: str, path: str, body=None, clock: str | None = None) -> tuple[int, object]:
    headers = {"Content-Type": "application/json"}
    if clock:
        headers["X-Test-Clock"] = clock
    data = None if body is None else json.dumps(body).encode("utf-8")
    request = urllib.request.Request(f"{URL}{path}", data=data, headers=headers, method=method)
    try:
        with urllib.request.urlopen(request, timeout=30) as response:
            return response.status, json.loads(response.read())
    except urllib.error.HTTPError as exc:
        return exc.code, json.loads(exc.read())


def commit(sha, at, change="CHG-1", reverts=None, branch="main"):
    return {"event_id": f"c-{sha}", "type": "commit", "at": at, "sha": sha, "branch": branch,
            "change_id": None if reverts else change, "reverts": reverts}


def deployment(dep_id, at, commits, outcome="success", environment="production"):
    return {"event_id": f"d-{dep_id}", "type": "deployment", "at": at, "deployment_id": dep_id,
            "environment": environment, "outcome": outcome, "commits": commits, "unplanned": False,
            "caused_by": None}


def metrics(events: list[dict]) -> dict:
    return dora.compute({"window": WINDOW, "events": events})


def flatten(value: dict, prefix: str = "") -> dict:
    flat = {}
    for key, item in value.items():
        flat.update(flatten(item, f"{prefix}{key}.") if isinstance(item, dict) else {f"{prefix}{key}": item})
    return flat


# --- the engine --------------------------------------------------------------------------------------------


def test_median_odd_even_and_empty():
    assert dora._median([Decimal(3), Decimal(1), Decimal(2)]) == 2
    assert dora._median([Decimal(1), Decimal(4)]) == Decimal("2.5")
    assert dora._median([]) is None


def test_rounding_is_half_up_not_bankers():
    assert dora._whole_seconds(Decimal("2.5")) == 3
    assert dora._whole_seconds(Decimal("4.5")) == 5
    assert dora._ratio(1, 8_000_000) == 0.0 and dora._ratio(5, 10_000_000) == 0.000001


def test_e1_negative_lead_time_is_clamped_and_counted():
    answer = metrics([commit("a", "2026-09-03T10:05:00Z"), deployment("D1", "2026-09-03T10:00:00Z", ["a"])])
    assert answer["change_lead_time_seconds_p50"] == 0
    assert answer["anomalies"]["negative_lead_time_pairs"] == 1
    assert answer["counts"]["lead_time_pairs"] == 1


def test_e2_revert_of_a_revert_is_one_change():
    events = [commit("a", "2026-09-02T00:00:00Z"), commit("b", "2026-09-03T00:00:00Z", reverts="a"),
              commit("c", "2026-09-04T00:00:00Z", reverts="b"), deployment("D1", "2026-09-05T00:00:00Z", ["a", "b", "c"])]
    answer = metrics(events)
    assert answer["counts"]["changes"] == 1
    assert answer["ground_truth"]["changes_delivered"] == 1
    assert answer["ground_truth"]["true_change_lead_time_seconds_p50"] == 3 * 86400
    assert answer["anomalies"]["revert_chains_collapsed"] == 2


def test_e3_e4_branch_ignored_and_empty_deployment_counted():
    events = [commit("h", "2026-09-03T00:00:00Z", branch="hotfix/1"), deployment("D1", "2026-09-03T01:00:00Z", ["h"]),
              deployment("D2", "2026-09-04T00:00:00Z", [], outcome="failure")]
    answer = metrics(events)
    assert answer["counts"]["lead_time_pairs"] == 1
    assert answer["anomalies"]["commits_never_on_main"] == 1
    assert answer["anomalies"]["deployments_without_commits"] == 1
    assert answer["change_fail_rate"] == 0.5


def test_e5_open_failure_is_not_given_a_recovery_time():
    events = [deployment("D1", "2026-09-03T00:00:00Z", [], outcome="failure"),
              {"event_id": "i1", "type": "incident", "at": "2026-09-03T00:10:00Z", "incident_id": "INC-1",
               "phase": "opened", "deployments": ["D1"]}]
    answer = metrics(events)
    assert answer["failed_deployment_recovery_time_seconds_p50"] is None
    assert answer["counts"]["open_failures"] == 1
    assert answer["change_fail_rate"] == 1.0


def test_staging_and_out_of_window_deployments_are_ignored():
    answer = metrics([deployment("D1", "2026-09-03T00:00:00Z", [], environment="staging"),
                      deployment("D2", "2026-09-22T00:00:00Z", [])])
    assert answer["counts"]["deployments"] == 0


def test_revert_of_a_missing_sha_is_rejected():
    with pytest.raises(ValidationError):
        metrics([commit("b", "2026-09-03T00:00:00Z", reverts="nope")])


# --- the running service -----------------------------------------------------------------------------------


def test_health():
    assert call("GET", "/health")[0] == 200


def test_practice_fixture_matches_published_values():
    status, answer = call("POST", "/dora/metrics", {"window": WINDOW, "events": practice_log()})
    assert status == 200
    got = flatten(answer)
    for field, want in flatten(practice_expected()).items():
        have = got[field]
        if isinstance(want, float) and have is not None:
            assert abs(have - want) <= 0.0005, field
        elif field.endswith("_seconds_p50") and want is not None:
            assert abs(have - want) <= 1, field
        else:
            assert have == want, field


def test_order_independence_and_duplicates():
    events = practice_log()
    _, once = call("POST", "/dora/metrics", {"window": WINDOW, "events": events})
    _, reversed_ = call("POST", "/dora/metrics", {"window": WINDOW, "events": events[::-1]})
    _, doubled = call("POST", "/dora/metrics", {"window": WINDOW, "events": events + events})
    assert once == reversed_ == doubled


def test_empty_log():
    status, answer = call("POST", "/dora/metrics", {"window": WINDOW, "events": []})
    assert status == 200 and answer["deployment_frequency_per_day"] == 0.0
    assert answer["change_fail_rate"] is None and answer["change_lead_time_seconds_p50"] is None
    assert set(answer["counts"].values()) == {0} and set(answer["anomalies"].values()) == {0}


@pytest.mark.parametrize("body", [
    {"window": {"from": "2026-09-02T00:00:00Z", "to": "2026-09-01T00:00:00Z"}, "events": []},
    {"events": []},
    {"window": WINDOW},
    {"window": WINDOW, "events": {}},
    [],
], ids=["empty-window", "no-window", "no-events", "events-not-array", "not-an-object"])
def test_rejections(body):
    status, answer = call("POST", "/dora/metrics", body)
    assert status in (400, 422) and "error" in answer


def test_ticket_events_phases_and_order():
    ticket = {"title": "lab2 stream", "reporter": {"name": "tester"}, "impact": 2, "urgency": 2}
    _, created = call("POST", "/tickets", ticket, clock="2026-10-14T10:00:00Z")
    ticket_id = created["id"]
    call("POST", f"/tickets/{ticket_id}/ack", clock="2026-10-14T10:05:00Z")
    call("POST", f"/tickets/{ticket_id}/start", clock="2026-10-14T10:06:00Z")
    call("POST", f"/tickets/{ticket_id}/resolve", clock="2026-10-14T11:00:00Z")

    status, stream = call("GET", "/dora/ticket-events")
    assert status == 200
    mine = [(e["phase"], e["state"]) for e in stream if e["ticket_id"] == ticket_id]
    assert mine == [("created", "new"), ("acknowledged", "acknowledged"), ("resolved", "resolved")]
    keys = [(dora.parse_instant(e["at"]), e["ticket_id"]) for e in stream]
    assert keys == sorted(keys)
