# ai-generated: 90% - Claude Code drafted from my choice of the gaming move, reviewed by me
"""Build gaming/after.jsonl from the practice log and check the three gates of lab2/METRIC-SPEC.md section 8.

    python gaming/make_after.py            (svcdesk must be running on localhost:8080)

The move games deployment_frequency_per_day through R-11, which counts production deployments of any content:
the last week's real releases are held back to a "release day" after the window, and the window is filled with
empty redeploys instead. Frequency goes up; the base work reaches production later, or not inside the window.
"""

import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "tools"))
from dora_post import post_metrics, read_log  # noqa: E402

BASE = os.path.join(ROOT, "fixtures", "events-practice.jsonl")
AFTER = os.path.join(ROOT, "gaming", "after.jsonl")
GAMING = os.path.join(ROOT, "gaming.json")

HELD_BACK = ("DEP-0031", "DEP-0037", "DEP-0039", "DEP-0040", "DEP-0041", "DEP-0042")
RELEASE_DAY = "2026-09-23"   # after the window's end (2026-09-22T00:00:00Z): later, never earlier (R-19)
EMPTY_REDEPLOYS = 20


def transform(base: list[dict]) -> list[dict]:
    after = []
    for event in base:
        event = dict(event)
        if event["type"] == "deployment" and event["deployment_id"] in HELD_BACK:
            event["at"] = RELEASE_DAY + event["at"][10:]   # same time of day, later date
        after.append(event)
    for n in range(1, EMPTY_REDEPLOYS + 1):
        # One empty, successful production redeploy roughly every 25 hours across the window.
        hour = 6 + (n - 1) * 25
        at = f"2026-09-{1 + hour // 24:02d}T{hour % 24:02d}:30:00Z"
        after.append({"event_id": f"d-g{n:03d}", "type": "deployment", "at": at, "deployment_id": f"DEP-G{n:03d}",
                      "environment": "production", "outcome": "success", "commits": [], "unplanned": False,
                      "caused_by": None})
    return after


def conserved(base: list[dict], after: list[dict]) -> list[str]:
    """R-19: base commits and incidents unchanged; base deployments keep id, outcome, environment, never earlier."""
    from datetime import datetime

    def instant(text: str) -> datetime:
        return datetime.fromisoformat(text.replace("Z", "+00:00"))

    problems = []
    commits = {e["sha"]: e for e in after if e["type"] == "commit"}
    incidents = {(e["incident_id"], e["phase"]): e for e in after if e["type"] == "incident"}
    deployments = {e["deployment_id"]: e for e in after if e["type"] == "deployment"}
    for event in base:
        if event["type"] == "commit":
            now = commits.get(event["sha"])
            if now is None or any(now[k] != event[k] for k in ("at", "sha", "branch", "change_id", "reverts")):
                problems.append(f"commit {event['sha']} changed")
        elif event["type"] == "incident":
            if incidents.get((event["incident_id"], event["phase"])) != event:
                problems.append(f"incident {event['incident_id']} {event['phase']} changed")
        else:
            now = deployments.get(event["deployment_id"])
            if now is None or now["outcome"] != event["outcome"] or now["environment"] != event["environment"]:
                problems.append(f"deployment {event['deployment_id']} changed id, outcome or environment")
            elif instant(now["at"]) < instant(event["at"]):
                problems.append(f"deployment {event['deployment_id']} moved earlier")
    return problems


def base_only(base: list[dict], after: list[dict]) -> list[dict]:
    """What the checker builds for R-21: commits not in the base removed, deployments' commits filtered."""
    shas = {e["sha"] for e in base if e["type"] == "commit"}
    out = []
    for event in after:
        if event["type"] == "commit" and event["sha"] not in shas:
            continue
        if event["type"] == "deployment":
            event = {**event, "commits": [sha for sha in event["commits"] if sha in shas]}
        out.append(event)
    return out


def main() -> None:
    base = read_log(BASE)
    after = transform(base)
    with open(AFTER, "w", encoding="utf-8", newline="\n") as handle:
        handle.writelines(json.dumps(event, separators=(",", ":")) + "\n" for event in after)

    problems = conserved(base, after)
    print("R-19 conservation:", "OK" if not problems else problems)

    before, answer = post_metrics(base), post_metrics(after)
    frequency = answer["deployment_frequency_per_day"] / before["deployment_frequency_per_day"] - 1
    print(f"R-20 deployment_frequency_per_day: {before['deployment_frequency_per_day']} -> "
          f"{answer['deployment_frequency_per_day']} ({frequency:+.1%}, needs +25.0%)")

    harmed = post_metrics(base_only(base, after))["ground_truth"]
    was = before["ground_truth"]
    delivered = harmed["changes_delivered"] / was["changes_delivered"]
    lead = harmed["true_change_lead_time_seconds_p50"] / was["true_change_lead_time_seconds_p50"]
    print(f"R-21 changes_delivered: {was['changes_delivered']} -> {harmed['changes_delivered']} "
          f"({delivered:.1%}, needs <= 90%); true lead time {lead:.1%} of base (or >= 125%)")

    with open(GAMING, "w", encoding="utf-8", newline="\n") as handle:
        json.dump({"metric": "deployment_frequency_per_day", "rule": "R-11", "before": before, "after": answer},
                  handle, indent=2)
        handle.write("\n")

    if problems or frequency < 0.25 or (delivered > 0.90 and lead < 1.25):
        sys.exit("a gate fails")


if __name__ == "__main__":
    main()
