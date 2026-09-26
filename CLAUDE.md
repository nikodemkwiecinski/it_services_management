<!-- ai-generated: 80% - drafted by Claude Code, reviewed by me -->
# svcdesk - guidance for Claude Code

`svcdesk` is the course's service-desk API: JSON over HTTP on port 8080, Python 3.13 + FastAPI + SQLite, shipped
as a Docker Compose project. The requirements are in `REQUIREMENTS.md` (R-01..R-25), the enforced contract in
`API.md`, the published checks in `CHECKS.md`, and the specification in `specs/001-svcdesk-ticketing-api/`.

Lab 2 (current) adds `POST /dora/metrics` and `GET /dora/ticket-events`. Its rulebook is `lab2/METRIC-SPEC.md`
(R-01..R-21 there are a different numbering from `REQUIREMENTS.md`), its checks `lab2/CHECKS.md`, its handout
`lab2/HANDOUT.md`; the practice log and its expected answer are in `fixtures/`.

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
- No bind mounts in `docker-compose.yml`, no network at run time: dependencies go in `requirements.txt` and are
  installed by the `Dockerfile`.
- Tags `lab1/vN` and `lab2/vN` are never moved or deleted; never create one without the user asking.
- No personal data (hostnames, usernames, diagnostic output) in the repository.

## Layout

- `src/svcdesk/main.py` routes and JSON error handlers; `clock.py` the per-request test clock; `validation.py`
  create-ticket rules; `priority.py` the matrix; `sla.py` both clocks, breach and pause; `lifecycle.py` the
  state machine and reopen window; `store.py` SQLite on `/data`.

## Commands

- Check everything: `.\itsmlab.ps1 verify 2` (Windows) or `./itsmlab.sh verify 2`; it must exit 0.
  Lab 1 still checks with `verify 1`, which must print `observations  C1=wallclock  C2=immutable  C3=matrix`.
- Run locally: `docker compose up --build --wait svcdesk`, then `http://localhost:8080/health`.
