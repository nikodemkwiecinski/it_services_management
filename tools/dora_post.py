# ai-generated: 90% - Claude Code drafted, reviewed by me
"""Post a JSONL event log to a running svcdesk's POST /dora/metrics and print (or save) the answer.

    python tools/dora_post.py fixtures/events-practice.jsonl --out metrics.json
    python tools/dora_post.py gaming/after.jsonl --compare fixtures/metrics-practice.json

The window defaults to the published one (lab2/METRIC-SPEC.md section 2).
"""

import argparse
import json
import sys
import urllib.error
import urllib.request

WINDOW = {"from": "2026-09-01T00:00:00Z", "to": "2026-09-22T00:00:00Z"}


def read_log(path: str) -> list[dict]:
    with open(path, encoding="utf-8") as handle:
        return [json.loads(line) for line in handle if line.strip()]


def post_metrics(events: list[dict], url: str = "http://localhost:8080", window: dict = WINDOW) -> dict:
    request = urllib.request.Request(
        f"{url}/dora/metrics",
        data=json.dumps({"window": window, "events": events}).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(request, timeout=30) as response:
            return json.loads(response.read())
    except urllib.error.HTTPError as exc:
        sys.exit(f"{exc.code}: {exc.read().decode('utf-8', 'replace')}")


def flatten(value: dict, prefix: str = "") -> dict:
    flat = {}
    for key, item in value.items():
        if isinstance(item, dict):
            flat.update(flatten(item, f"{prefix}{key}."))
        else:
            flat[f"{prefix}{key}"] = item
    return flat


def differences(expected: dict, actual: dict) -> list[str]:
    """Fields outside the R-18 tolerances: seconds +-1, ratios +-0.0005, counts exact, null only null."""
    got = flatten(actual)
    out = []
    for field, want in flatten(expected).items():
        have = got.get(field)
        if want is None or have is None or isinstance(want, str):
            same = want == have
        elif field.startswith(("counts.", "anomalies.")) or field == "ground_truth.changes_delivered":
            same = want == have
        elif field.endswith("_seconds_p50"):
            same = abs(have - want) <= 1
        else:
            same = abs(have - want) <= 0.0005
        if not same:
            out.append(f"{field}: expected {want}, got {have}")
    return out


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("log", help="a JSONL event log")
    parser.add_argument("--url", default="http://localhost:8080")
    parser.add_argument("--out", help="write the answer to this file")
    parser.add_argument("--compare", help="a metric object to compare the answer with, within R-18")
    args = parser.parse_args()

    answer = post_metrics(read_log(args.log), args.url)
    text = json.dumps(answer, indent=2) + "\n"
    if args.out:
        with open(args.out, "w", encoding="utf-8", newline="\n") as handle:
            handle.write(text)
    else:
        sys.stdout.write(text)
    if args.compare:
        with open(args.compare, encoding="utf-8") as handle:
            problems = differences(json.load(handle), answer)
        for problem in problems:
            print("MISMATCH", problem, file=sys.stderr)
        print(f"{len(problems)} field(s) differ from {args.compare}", file=sys.stderr)
        sys.exit(1 if problems else 0)


if __name__ == "__main__":
    main()
