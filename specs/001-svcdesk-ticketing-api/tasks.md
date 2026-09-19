<!-- ai-generated: 85% - drafted by Claude Code via the speckit-tasks workflow, reviewed by me -->
# Tasks: svcdesk ticketing API

**Input**: [plan.md](plan.md), [spec.md](spec.md), [data-model.md](data-model.md), [research.md](research.md),
[contracts/README.md](contracts/README.md), [quickstart.md](quickstart.md)

**Tests**: no separate test suite was requested (Stretch S3 is not chosen); validation is the published
checker plus a local check of the vectors T1..T8.

## Phase 1: Setup

- [X] T001 Create the package `src/svcdesk/__init__.py` with the AI-disclosure header
- [X] T002 [P] Pin dependencies in `requirements.txt` (fastapi 0.141.1, uvicorn 0.52.4, tzdata 2026.4)
- [X] T003 [P] Create `Dockerfile` from `Dockerfile.example` (python:3.13-slim, deps at build, `/data`, port 8080)
- [X] T004 Enable the healthcheck of the `svcdesk` service in `docker-compose.yml`

## Phase 2: Foundational (blocks every story)

- [X] T005 [P] Record the decisions C1 = wallclock, C2 = immutable, C3 = matrix in `src/svcdesk/decisions.py`
- [X] T006 [P] Implement strict RFC 3339 clock parsing, `now()` and UTC `Z` formatting in `src/svcdesk/clock.py`
- [X] T007 [P] Implement SQLite persistence (create, get, list, update under a lock) in `src/svcdesk/store.py`
- [X] T008 Create the FastAPI app with JSON error handlers (404, 405, 422) and the clock middleware in `src/svcdesk/main.py`
- [X] T009 Implement `GET /health` in `src/svcdesk/main.py` (R-02)

**Checkpoint**: `docker compose up --wait` and `/health` answer 200 (L1-CORE-1).

## Phase 3: User Story 1 - Raise a ticket and get a computed priority (P1)

- [X] T010 [P] [US1] Implement create-ticket validation (R-03, R-20) in `src/svcdesk/validation.py`
- [X] T011 [P] [US1] Implement the priority matrix with C3 in `src/svcdesk/priority.py`
- [X] T012 [US1] Implement `POST /tickets`, `GET /tickets/{id}` and `GET /tickets?state=&priority=` in `src/svcdesk/main.py`

**Checkpoint**: checks 2.03-2.23 and 2.46-2.48 pass.

## Phase 4: User Story 4 - Know which tickets are late (P1)

- [X] T013 [US4] Implement wall-clock and business-hours due instants with C1 and the tie rule in `src/svcdesk/sla.py`
- [X] T014 [US4] Compute the `sla` block at creation in `src/svcdesk/main.py`
- [X] T015 [US4] Implement breach and pause and `GET /tickets/{id}/sla` in `src/svcdesk/sla.py` and `src/svcdesk/main.py`
- [X] T016 [US4] Check T1..T8 against `src/svcdesk/sla.py` inside the built image

**Checkpoint**: checks 2.36-2.45 pass.

## Phase 5: User Story 2 - Work a ticket through its life cycle (P1)

- [X] T017 [US2] Implement the transition table and timestamps in `src/svcdesk/lifecycle.py`
- [X] T018 [US2] Implement `POST /tickets/{id}/ack|start|resolve|close` in `src/svcdesk/main.py`

**Checkpoint**: checks 2.24-2.31 and 2.49 pass.

## Phase 6: User Story 3 - Reopen a fix that did not work (P2)

- [X] T019 [US3] Implement reopen with the 7-day window and C2 in `src/svcdesk/lifecycle.py`
- [X] T020 [US3] Implement `POST /tickets/{id}/reopen` in `src/svcdesk/main.py`

**Checkpoint**: checks 2.32-2.35 pass.

## Phase 7: User Story 5 - Operate and test the desk (P2)

- [X] T021 [US5] Verify restart survival: create, `docker compose restart svcdesk`, read back (R-23)

## Phase 8: Polish and cross-cutting

- [X] T022 Run `.\itsmlab.ps1 verify 1` until every Core spec passes and `observations` equals `DECISIONS.md`
- [X] T023 [P] Stretch S2: `CLAUDE.md`, `.claude/agents/reviewer.md` with `disallowedTools`, `AGENT-POLICY.md`
- [X] T024 Stretch S1: run converge and save the comparison to `specs/converge.md`
- [X] T025 Confirm the AI-disclosure header on every checked file under `src/` and `specs/` and in `DECISIONS.md`

## Dependencies and execution order

- Phase 1 then Phase 2 block everything; T005-T007 are parallel.
- US1 (Phase 3) before US4 (Phase 4): the `sla` block is attached at creation.
- US2 (Phase 5) before US3 (Phase 6): reopen needs resolved and closed tickets.
- Phase 8 last. MVP scope: Phases 1-3 (health, create, read, list, priority).
