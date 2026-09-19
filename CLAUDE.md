<!-- ai-generated: 80% - drafted by Claude Code, reviewed by me -->
# svcdesk - guidance for Claude Code

`svcdesk` is the course's service-desk API: JSON over HTTP on port 8080, Python 3.13 + FastAPI + SQLite, shipped
as a Docker Compose project. The requirements are in `REQUIREMENTS.md` (R-01..R-25), the enforced contract in
`API.md`, the published checks in `CHECKS.md`, and the specification in `specs/001-svcdesk-ticketing-api/`.

## Rules that are graded

- `API.md` is the contract. Do not change a path, field, status code or error shape to make code simpler.
- The decisions C1 = `wallclock`, C2 = `immutable`, C3 = `matrix` live in `src/svcdesk/decisions.py` and must
  equal the front matter of `DECISIONS.md`. Change both, and the spec, in the same commit or not at all.
- Every file under `src/` and `specs/` with extension `.py .go .ts .js .java .cs .rb .rs .kt .md`, and
  `DECISIONS.md`, starts with an `ai-generated: <0-100>% - <how>` comment in its first ten lines.
- No bind mounts in `docker-compose.yml`, no network at run time: dependencies go in `requirements.txt` and are
  installed by the `Dockerfile`.
- Tags `lab1/vN` are never moved or deleted; never create one without the user asking.
- No personal data (hostnames, usernames, diagnostic output) in the repository.

## Layout

- `src/svcdesk/main.py` routes and JSON error handlers; `clock.py` the per-request test clock; `validation.py`
  create-ticket rules; `priority.py` the matrix; `sla.py` both clocks, breach and pause; `lifecycle.py` the
  state machine and reopen window; `store.py` SQLite on `/data`.

## Commands

- Check everything: `.\itsmlab.ps1 verify 1` (Windows) or `./itsmlab.sh verify 1`; it must exit 0 and print
  `observations  C1=wallclock  C2=immutable  C3=matrix`.
- Run locally: `docker compose up --build --wait svcdesk`, then `http://localhost:8080/health`.
