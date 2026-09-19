<!-- ai-generated: 85% - drafted by Claude Code via the speckit-plan workflow (Phase 1), reviewed by me -->
# Data Model: svcdesk ticketing API

## Ticket

| field | type | source | rules |
|---|---|---|---|
| `id` | string | service | UUID4, opaque, unique (R-18) |
| `title` | string | client | required, 1..200 characters |
| `description` | string | client | optional, 0..4000, default `""` (null treated as absent) |
| `reporter.name` | string | client | required, 1..100 characters |
| `reporter.email` | string or null | client | optional, default null, not format-checked |
| `reporter.vip` | boolean | client | optional, default false; stored, no effect on priority (C3 = `matrix`) |
| `impact`, `urgency` | integer | client | required, integer 1..3; booleans, strings and floats are rejected |
| `related_to` | string or null | client | optional, default null; existence not validated in Lab 1 |
| `priority` | `P1`..`P4` | service | impact/urgency matrix (R-04, R-05) |
| `state` | enum | service | see state machine |
| `created_at` | instant | service | "now" of the create request |
| `acknowledged_at`, `resolved_at`, `closed_at` | instant or null | service | "now" of the action; reopen clears `resolved_at` and `closed_at` |
| `sla.ack_due_at`, `sla.resolve_due_at` | instant | service | fixed at creation, never recomputed (R-11) |

Server-owned fields and unknown fields in a request body are ignored. A validation failure answers 422 with
`{"error": {"code": "validation", "message": "..."}}`.

## Priority matrix

| impact \ urgency | 1 | 2 | 3 |
|---|---|---|---|
| 1 | P1 | P2 | P3 |
| 2 | P2 | P3 | P4 |
| 3 | P3 | P4 | P4 |

## SLA targets and clocks

| priority | ack | resolve | clock |
|---|---|---|---|
| P1 | 15 min | 4 h | wall clock (C1 = `wallclock`) |
| P2 | 1 h | 8 h | business hours |
| P3 | 4 h | 24 h | business hours |
| P4 | 8 h | 72 h | business hours |

Business hours: Monday to Friday, [08:00, 16:00) Europe/Warsaw; tie rule: a target ending exactly at 16:00 is
due at 16:00 that day.

## SLA view (derived per request)

- `ack_breached` = (`acknowledged_at` is null and `now > ack_due_at`) or `acknowledged_at > ack_due_at`
- `resolve_breached` = (`resolved_at` is null and `now > resolve_due_at`) or `resolved_at > resolve_due_at`
- `paused` = state not in {`resolved`, `closed`} and the ticket's resolution clock is business hours and `now`
  is outside a business window; always false for P1.

## State machine

| action | from | to | side effect | otherwise |
|---|---|---|---|---|
| ack | new | acknowledged | `acknowledged_at = now` | 409 `invalid_transition` |
| start | acknowledged | in_progress | - | 409 `invalid_transition` |
| resolve | in_progress | resolved | `resolved_at = now` | 409 `invalid_transition` |
| close | resolved | closed | `closed_at = now` | 409 `invalid_transition` |
| reopen | resolved, if `now <= resolved_at + 7 days` | in_progress | clear `resolved_at`, `closed_at` | 409 `reopen_window_expired` (resolved, too late), 409 `ticket_closed` (closed, C2 = `immutable`), 409 `invalid_transition` (other states) |

An action on an unknown id answers 404 `not_found`. The request clock is never compared with stored
timestamps except in the reopen window rule.
