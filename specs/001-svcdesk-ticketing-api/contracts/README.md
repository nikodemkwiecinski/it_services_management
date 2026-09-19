<!-- ai-generated: 90% - drafted by Claude Code via the speckit-plan workflow (Phase 1), reviewed by me -->
# Interface contract

The external interface is defined in [API.md](../../../API.md) at the repository root, sections 1 to 9; it is
the contract the checker enforces and is not restated here, so that there is one source of truth
(constitution principle I).

Where API.md lists two admissible behaviours, this service implements:

| decision | API.md section | behaviour implemented |
|---|---|---|
| C1 = `wallclock` | 4 | both P1 targets are `created_at + target`; P2..P4 on business hours; `paused` is always false for P1 |
| C2 = `immutable` | 6 | reopen only from `resolved` within 7 days of `resolved_at`; reopen on `closed` is 409 at any age |
| C3 = `matrix` | 3 | priority from the matrix only; impact 3, urgency 3, VIP true is `P4` |

Error codes returned (recommended by API.md, not checked in Lab 1): `validation` (422), `invalid_clock` (422),
`not_found` (404), `method_not_allowed` (405), `invalid_transition`, `reopen_window_expired`, `ticket_closed`
(409).
