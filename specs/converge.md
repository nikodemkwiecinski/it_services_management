<!-- ai-generated: 85% - produced by Claude Code running the speckit-converge workflow and saved to this file; reviewed by me -->
# Convergence report: svcdesk ticketing API

Workflow: `speckit-converge` on `specs/001-svcdesk-ticketing-api` (spec.md, plan.md, tasks.md, constitution
v1.0.0), after the implementation pass and a green `itsmlab verify 1` run (every Core spec `pass`, L1-CORE-5
`skip`, observations `C1=wallclock C2=immutable C3=matrix`).

**Outcome: converged.** No actionable finding; `tasks.md` was left unchanged by the workflow.

## Requirements checked against the code

| requirement | where it is implemented | evidence | status |
|---|---|---|---|
| R-01, R-25 JSON API on 8080, JSON 404 | `main.py` exception handler, `Dockerfile` CMD | check 2.02; unknown path answers `{"error": {"code": "not_found"}}` | met |
| R-02 health | `main.py` `/health` | checks 1.04, 2.01 | met |
| R-03, R-20 validation, ignored fields | `validation.py` on the raw body, 422 `validation` | checks 2.16-2.19, 2.48 | met |
| R-04, R-05 matrix only | `priority.py` `MATRIX` | checks 2.07-2.15 | met |
| R-06 VIP floor | rejected by C3 = `matrix`; flag stored and returned | checks 2.46, 2.47 (`P4`, `P1`) | met as decided |
| R-07, R-08 life cycle, 409, 404 | `lifecycle.py` `TRANSITIONS` | checks 2.24-2.31, 2.49 | met |
| R-09, R-10, R-11 closed, reopen window | `lifecycle.py` reopen branch, C2 = `immutable` | checks 2.32-2.35 | met as decided |
| R-12, R-13 targets, business hours | `sla.py` `add_business_time`, tie rule at 16:00 | T1..T8 reproduced in the image; checks 2.36-2.40 | met |
| R-14 P1 around the clock | `sla.py` `uses_business_clock`, C1 = `wallclock` | check 2.41 (15:15Z / 19:00Z) | met as decided |
| R-15, R-16 SLA view, breach, pause | `sla.py` `status`, `main.py` `/sla` | checks 2.42-2.45 | met |
| R-17 UTC `Z` instants | `clock.py` `format_instant` | check 2.03 | met |
| R-18 opaque ids | `main.py` UUID4 | check 2.06 | met |
| R-19 list with exact filters | `main.py` `list_tickets` | checks 2.22, 2.23 | met |
| R-21 test clock | `clock.py` strict RFC 3339 with offset, middleware | checks 2.03, 2.04 | met |
| R-22, R-24 compose, no bind mounts, 120 s | `docker-compose.yml`, `Dockerfile`, healthcheck | checks 1.01-1.04 | met |
| R-23 restart survival | `store.py` SQLite on the `svcdesk-data` volume | ticket read back after `docker compose restart` | met |

## Plan and constitution

The plan's structure (`src/svcdesk/` modules, SQLite, FastAPI with hand-written validation) is what was built.
Constitution principles I to V hold: API.md is followed, the specs receipt precedes every `src/` commit,
`decisions.py` equals the `DECISIONS.md` front matter, "now" is resolved once per request, and the image needs
no network at run time. FastAPI is a dependency beyond the standard library; the plan's research justifies it
(JSON error handlers and routing), so it is not a gap.

## Low-risk additions (not gaps)

- Error codes `invalid_clock` and `method_not_allowed` extend the recommended list; codes are not checked in
  Lab 1.
- `related_to` must be a string or null; its existence is not validated, as the spec's assumptions state.
