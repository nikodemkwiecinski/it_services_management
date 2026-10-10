<!-- ai-generated: 80% - drafted by Claude Code, reviewed by me -->
# svcdesk - guidance for Claude Code

`svcdesk` is the course's service-desk API: JSON over HTTP on port 8080, Python 3.13 + FastAPI + SQLite, shipped
as a Docker Compose project. The requirements are in `REQUIREMENTS.md` (R-01..R-25), the enforced contract in
`API.md`, the published checks in `CHECKS.md`, and the specification in `specs/001-svcdesk-ticketing-api/`.

Lab 2 adds `POST /dora/metrics` and `GET /dora/ticket-events`. Its rulebook is `lab2/METRIC-SPEC.md`
(R-01..R-21 there are a different numbering from `REQUIREMENTS.md`), its checks `lab2/CHECKS.md`, its handout
`lab2/HANDOUT.md`; the practice log and its expected answer are in `fixtures/`.

Lab 3 (current) adds `GET /kb/search` (calls the course image `kb-index`), the request histogram and `GET /metrics`,
`slo.md`, `ai-first-draft.md`, `prometheus/` (alerts and their promtool tests) and `grafana/`. Its rulebook is
`lab3/MONITORING-SPEC.md` (M-01..M-31), its checks `lab3/CHECKS.md`, its handout `lab3/HANDOUT.md`.

## Rules that are graded

- `API.md` is the contract. Do not change a path, field, status code or error shape to make code simpler.
- `lab2/METRIC-SPEC.md` wins over any "usual" DORA definition, above all on the six edge cases E1..E6.
- The decisions C1 = `wallclock`, C2 = `immutable`, C3 = `matrix` live in `src/svcdesk/decisions.py` and must
  equal the front matter of `DECISIONS.md`. Change both, and the spec, in the same commit or not at all.
- The counts in the front matter of `EDGE-CASES.md` must equal what the service reports for the practice
  fixture; `metrics.json` and `gaming.json` hold the service's own answers, never hand-written numbers.
- Every file under `src/`, `specs/` and `metrics/` with extension `.py .go .ts .js .java .cs .rb .rs .kt .md`,
  and `DECISIONS.md` and `EDGE-CASES.md`, carries an `ai-generated: <0-100>% - <how>` comment in its first ten
  lines (in `EDGE-CASES.md` on the line right after the front matter).
- `PREDICTION.md` (Stretch 1) is never edited after its receipt.
- Lab 3: the ladder in `src/svcdesk/metrics.py` must resolve the measured p99 (M-11), and `slo.md`'s
  `threshold_seconds` must be one of its boundaries; `ai-first-draft.md`'s `## Prompt` and `## Answer` are verbatim
  and never edited; the thresholds in `prometheus/alerts.yml` are constants, equal to `slo.md`'s burn rates and
  objective; after changing a rule, re-find the test edges with promtool so that every mutant still fails.
- No bind mounts in `docker-compose.yml`, no network at run time: dependencies go in `requirements.txt` and are
  installed by the `Dockerfile`.
- Tags `lab1/vN`, `lab2/vN` and `lab3/vN` are never moved or deleted; never create one without the user asking.
- No personal data (hostnames, usernames, diagnostic output) in the repository.

## Layout

- `src/svcdesk/main.py` routes and JSON error handlers; `clock.py` the per-request test clock; `validation.py`
  create-ticket rules; `priority.py` the matrix; `sla.py` both clocks, breach and pause; `lifecycle.py` the
  state machine and reopen window; `store.py` SQLite on `/data`; `kb.py` the call to `kb-index`; `metrics.py`
  the request histogram, its ladder and the timing middleware.

## Commands

- Check everything: `.\itsmlab.ps1 verify 3` (Windows) or `./itsmlab.sh verify 3`; it must exit 0. Measure only:
  `.\itsmlab.ps1 load 3`. Lab 2 still checks with `verify 2`.
  Lab 1 still checks with `verify 1`, which must print `observations  C1=wallclock  C2=immutable  C3=matrix`.
- Run locally: `docker compose up --build --wait svcdesk kb-index`, then `http://localhost:8080/health`; with
  `--profile observability` also Prometheus on :9090 and Grafana on :3000 (configuration baked into their images).
- promtool: `docker run --rm -v "${PWD}/prometheus:/p" -w /p --entrypoint promtool prom/prometheus:v3.15.0 test rules alerts_test.yml`.
