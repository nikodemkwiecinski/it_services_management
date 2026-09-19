<!-- ai-generated: 85% - drafted by Claude Code via the speckit-plan workflow, reviewed by me -->
# Implementation Plan: svcdesk ticketing API

**Branch**: `001-svcdesk-ticketing-api` (work on `main`) | **Date**: 2026-09-19 | **Spec**: [spec.md](spec.md)

**Input**: Feature specification from `specs/001-svcdesk-ticketing-api/spec.md`

## Summary

A small JSON-over-HTTP ticketing service on port 8080: ticket intake with validation, a priority computed from
the impact/urgency matrix (C3 = `matrix`), a five-state life cycle with a 7-day reopen window from `resolved`
only (C2 = `immutable`), and SLA due instants computed at creation on two clocks: wall clock for P1
(C1 = `wallclock`) and a Europe/Warsaw business-hours clock for P2..P4. A per-request test clock drives "now".
Tickets are stored in SQLite on a named volume; the service ships as a Docker Compose project.

## Technical Context

**Language/Version**: Python 3.13 (`python:3.13-slim`, Debian-based, ships the IANA tz database)

**Primary Dependencies**: FastAPI 0.141.1 (routing, JSON responses, exception handlers), uvicorn 0.52.4 (ASGI
server), tzdata 2026.4 (fallback tz database for `zoneinfo`). Validation is hand-written on the raw JSON body so
that error bodies and the int-only rules match API.md exactly; no Pydantic request models.

**Storage**: SQLite via the standard library `sqlite3`, file `/data/svcdesk.db` (env `SVCDESK_DB`) on the
named volume `svcdesk-data`; one row per ticket, the ticket document stored as JSON.

**Testing**: the published checker (`itsmlab verify 1`, 49 HTTP checks) plus a local vector check of T1..T8
against the SLA module.

**Target Platform**: Linux container (Docker Compose), no network after build.

**Project Type**: web service (single project).

**Performance Goals**: every request well under the checker's 10 s limit; `/health` within 120 s of `up`.

**Constraints**: responses always JSON; instants UTC with `Z`; test clock per request only; no bind mounts.

**Scale/Scope**: about 400 people, at most a few thousand tickets; the checker creates at most 100 per run, so
list filtering is done in memory without pagination.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| principle | how the plan satisfies it | status |
|---|---|---|
| I. The contract is API.md | routes, fields, status codes and error bodies are taken from API.md sections 1-8; `contracts/` points to API.md instead of restating it | pass |
| II. Specification before code | `spec.md` receipted at commit `4e314a6`; every file under `src/` is added after it | pass |
| III. Declared decisions equal observed behaviour | C1/C2/C3 are constants in one module (`src/svcdesk/decisions.py`) whose values equal the `DECISIONS.md` front matter | pass |
| IV. Deterministic time | a single `now` per request from `X-Test-Clock` (strict RFC 3339 with offset) or UTC; `zoneinfo("Europe/Warsaw")`; UTC `Z` output | pass |
| V. Self-contained and simple | dependencies installed at image build; SQLite from the standard library; named volume only | pass |

Post-design re-check (after Phase 1): unchanged, all pass. No complexity to justify.

## Project Structure

### Documentation (this feature)

```text
specs/001-svcdesk-ticketing-api/
├── spec.md              # receipted specification
├── plan.md              # this file
├── research.md          # Phase 0: technical decisions
├── data-model.md        # Phase 1: ticket entity, validation, state machine
├── quickstart.md        # Phase 1: how to run and validate
├── contracts/README.md  # Phase 1: pointer to API.md and the resolved decision behaviours
├── checklists/requirements.md
└── tasks.md             # Phase 2 (/speckit-tasks)
```

### Source Code (repository root)

```text
src/svcdesk/
├── __init__.py
├── main.py          # FastAPI app: routes, exception handlers, JSON error bodies, clock middleware
├── decisions.py     # C1 = wallclock, C2 = immutable, C3 = matrix (single source of truth)
├── clock.py         # parse X-Test-Clock, now(), UTC formatting
├── validation.py    # create-ticket body validation (R-03, R-20)
├── priority.py      # impact/urgency matrix (+ C3)
├── sla.py           # wall-clock and business-hours due instants, breach, pause (+ C1)
├── lifecycle.py     # transitions and reopen window (+ C2)
└── store.py         # SQLite persistence
Dockerfile           # from Dockerfile.example, plus healthcheck support
requirements.txt     # pinned dependencies
docker-compose.yml   # template contract, healthcheck enabled
```

**Structure Decision**: single web-service project under `src/svcdesk/`, matching the module path
`svcdesk.main:app` that `Dockerfile.example` starts. Pure logic (priority, SLA, life cycle, validation, clock) is
kept free of HTTP so it can be checked against the vectors directly.

## Complexity Tracking

No constitution violations; nothing to justify.
