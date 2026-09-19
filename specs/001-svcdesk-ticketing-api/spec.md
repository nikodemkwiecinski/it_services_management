<!-- ai-generated: 85% - drafted by Claude Code via the speckit-specify workflow from REQUIREMENTS.md and API.md; conflict resolutions chosen by me -->
# Feature Specification: svcdesk ticketing API

**Feature Branch**: `001-svcdesk-ticketing-api` (specification directory; work stays on `main`)

**Created**: 2026-09-19

**Status**: Draft

**Input**: User description: "svcdesk service desk ticketing API with priority matrix and SLA clocks, built from
REQUIREMENTS.md (R-01..R-25) and the interface contract API.md, resolving the three conflicting requirement
pairs C1, C2 and C3."

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Raise a ticket and get a computed priority (Priority: P1)

A desk agent, the monitoring system or an integration submits a ticket with a title, a reporter, an impact and
an urgency. The desk answers with the stored ticket, a service-assigned identifier, a priority computed from
the impact/urgency matrix and the two SLA due instants. Invalid submissions are refused with an explanation, so
that nothing incomplete reaches the Monday report.

**Why this priority**: Without ticket intake there is no desk; everything else operates on created tickets.

**Independent Test**: Create tickets for all nine impact/urgency combinations and one invalid ticket per
validation rule; read them back by id and through the filtered list.

**Acceptance Scenarios**:

1. **Given** the desk is running, **When** a ticket with impact 2 and urgency 1 is submitted, **Then** it is
   stored with state `new`, priority `P2`, a non-empty unique id and `created_at` equal to "now".
2. **Given** a submission without a title, with a 201-character title, with impact 5 or with urgency `"high"`,
   **When** it is submitted, **Then** it is refused with 400 or 422 and a JSON body carrying an `error` object.
3. **Given** a submission that also carries `priority: "P1"`, `id`, `state` or unknown fields, **When** it is
   submitted, **Then** those fields are ignored and the ticket is created normally.
4. **Given** created P1 and P4 tickets, **When** the list is filtered by `priority=P1` or `state=new`,
   **Then** only matching tickets are returned, all in one array.

---

### User Story 2 - Work a ticket through its life cycle (Priority: P1)

An agent acknowledges a new ticket, starts work, resolves it and closes it once the reporter confirms the fix.
Each step is a separate action and the desk records when acknowledgement, resolution and closure happened.
Shortcuts are refused so the recorded history is always complete.

**Why this priority**: The state history feeds the SLA breach calculation and the reports.

**Independent Test**: Drive fresh tickets through every allowed transition and attempt every forbidden one.

**Acceptance Scenarios**:

1. **Given** a `new` ticket, **When** it is acknowledged, **Then** state is `acknowledged` and
   `acknowledged_at` equals "now"; acknowledging it again answers 409.
2. **Given** a `new` ticket, **When** start, resolve or close is requested, **Then** each answers 409.
3. **Given** an `acknowledged` ticket, **When** resolve is requested without start, **Then** it answers 409.
4. **Given** an `in_progress` ticket, **When** it is resolved and then closed, **Then** `resolved_at` and
   `closed_at` equal the "now" of each request.
5. **Given** an unknown ticket id, **When** any action is requested, **Then** it answers 404 with an `error`
   object.

---

### User Story 3 - Reopen a fix that did not work (Priority: P2)

A reporter whose problem came back asks for the resolved ticket to be reopened. Within 7 days of the resolution
the ticket returns to `in_progress`; later, or once the ticket is closed, the reporter raises a new ticket that
references the old one through `related_to` (decision C2 = `immutable`).

**Why this priority**: Reopening protects the reporter; refusing it for closed tickets protects the record.

**Independent Test**: Resolve a ticket and reopen it 6 days later (200) and 7 days + 1 s later (409); close a
ticket and reopen it 1 day later (409); reopen a `new` ticket (409).

**Acceptance Scenarios**:

1. **Given** a ticket resolved 6 days ago, **When** reopen is requested, **Then** state is `in_progress`,
   `resolved_at` and `closed_at` are cleared and the resolution due instant is unchanged.
2. **Given** a ticket resolved 7 days and 1 second ago, **When** reopen is requested, **Then** it answers 409.
3. **Given** a ticket closed 1 day ago, **When** reopen is requested, **Then** it answers 409 regardless of age.

---

### User Story 4 - Know which tickets are late (Priority: P1)

The desk lead asks, for any ticket, what its priority is, when acknowledgement and resolution are due, whether
either target is breached and whether the clock is currently paused, so the Monday report is one call per
ticket.

**Why this priority**: "Nobody can say at 09:00 on Monday which tickets are late" is the reason for the project.

**Independent Test**: Create the published vectors T1..T8 with the test clock and compare both due instants;
query breach and pause at chosen instants.

**Acceptance Scenarios**:

1. **Given** vectors T1..T8 (API.md section 4), **When** each ticket is created at its `created_at`, **Then**
   `ack_due_at` and `resolve_due_at` equal the published values: the business-hours columns for P2..P4 and the
   wall-clock columns for P1 (decision C1 = `wallclock`).
2. **Given** a T2 ticket never acknowledged, **When** SLA is queried at 2026-10-19T09:31:00Z, **Then**
   `ack_breached` is true and `resolve_breached` false; at 2026-10-19T09:00:00Z `ack_breached` is false.
3. **Given** a T2 ticket acknowledged at 2026-10-16T13:45:00Z, **When** SLA is queried on Monday at 12:00Z,
   **Then** `ack_breached` is false.
4. **Given** an open T2 ticket, **When** SLA is queried on Saturday 2026-10-17T10:00:00Z, **Then** `paused` is
   true; on Monday 2026-10-19T09:00:00Z it is false.

---

### User Story 5 - Operate and test the desk (Priority: P2)

Operations start the desk with one compose command, monitoring polls its health, and testers pin "now" per
request to reproduce SLA scenarios.

**Independent Test**: `docker compose up --wait` then `GET /health`; create a ticket with an `X-Test-Clock`
header and compare `created_at`; send a malformed clock header.

**Acceptance Scenarios**:

1. **Given** the compose project, **When** it is started, **Then** `GET /health` answers 200
   `{"status":"ok","service":"svcdesk"}` within 120 seconds, with no network access after the build.
2. **Given** the test clock is enabled, **When** a request carries `X-Test-Clock: yesterday`, **Then** it is
   refused with 400 or 422.
3. **Given** the desk restarts, **When** a ticket created before the restart is read, **Then** it is returned.

### Edge Cases

- A target that ends exactly at 16:00 local is due at 16:00 that day, not 08:00 the next (T4).
- A business-hours target spanning the weekend on which DST ends (T8) counts only business hours, in local time.
- A ticket created before 08:00, after 16:00 or at the weekend starts its business clock at the next opening.
- An event exactly at the due instant is not a breach.
- A reopened ticket counts as not resolved again, against its original resolution target.
- Request clocks may go backwards between requests; the desk never rejects an action for that reason.
- `impact: true`, `impact: "2"` or `impact: 2.5` are not integers in 1..3 and are refused.
- An unknown path answers 404 with a JSON body; a wrong method on a known path answers 404 or 405.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001** (R-01, R-25): The desk MUST expose an HTTP API on port 8080 whose requests and responses are JSON;
  unknown paths MUST answer 404 with a JSON body.
- **FR-002** (R-02): `GET /health` MUST answer 200 with `{"status": "ok", "service": "svcdesk"}`.
- **FR-003** (R-03, R-20): Ticket creation MUST validate title (1..200), description (0..4000, default ""),
  reporter name (1..100), optional e-mail (default null), optional VIP flag (default false), impact and urgency
  (integers 1..3), optional `related_to` (not validated). Violations MUST answer 400 or 422 with an `error`
  object. Server-owned and unknown fields MUST be ignored.
- **FR-004** (R-04, R-05): Priority MUST be computed from the impact/urgency matrix and nothing else; a
  `priority` sent by the client MUST be ignored.
- **FR-005** (R-06, C3): The VIP flag MUST be stored and returned but MUST NOT change the priority
  (impact 3, urgency 3, VIP true is `P4`; impact 1, urgency 1, VIP true is `P1`).
- **FR-006** (R-07, R-08): The life cycle MUST be `new` -> `acknowledged` -> `in_progress` -> `resolved` ->
  `closed`, one endpoint per action, recording `acknowledged_at`, `resolved_at` and `closed_at`. Every other
  transition MUST answer 409 with an `error` object; an unknown ticket MUST answer 404.
- **FR-007** (R-09, R-10, R-11, C2): Reopen MUST be allowed only from `resolved`, while
  `now <= resolved_at + 7 days`, returning the ticket to `in_progress` and clearing `resolved_at` and
  `closed_at`. Reopen from `closed` MUST answer 409 regardless of age. Reopening MUST NOT change any due
  instant.
- **FR-008** (R-12, R-13): Each priority MUST have an acknowledgement and a resolution target (P1 15 min / 4 h,
  P2 1 h / 8 h, P3 4 h / 24 h, P4 8 h / 72 h) measured from creation. P2..P4 targets MUST run on the
  business-hours clock: Monday to Friday, [08:00, 16:00) Europe/Warsaw, DST-aware, with the closing-time tie
  rule of API.md section 4.
- **FR-009** (R-14, C1): Both P1 targets MUST run on the wall clock: `created_at + target`, around the clock.
- **FR-010** (R-15, R-16): `GET /tickets/{id}/sla` MUST return `priority`, `ack_due_at`, `resolve_due_at`,
  `ack_breached`, `resolve_breached` and `paused`, evaluated at "now", using strict "after" for breach and the
  pause rule of API.md section 5 (always false for wall-clock tickets).
- **FR-011** (R-17): Every instant MUST be RFC 3339; the desk MUST report instants in UTC with a `Z` suffix.
- **FR-012** (R-18): Ticket ids MUST be opaque, unique, non-empty and assigned by the desk.
- **FR-013** (R-19): `GET /tickets` MUST return every ticket matching the optional exact filters `state` and
  `priority` in one array, without pagination.
- **FR-014** (R-21): When `SVCDESK_TEST_CLOCK` is `1` or `true`, an `X-Test-Clock` header with an RFC 3339
  instant including an offset MUST be used as "now" for that request only; a header that does not parse MUST
  answer 400 or 422. Without the header, or when the variable is unset or `0`, "now" is real UTC time.
- **FR-015** (R-22, R-24): The desk MUST ship as a Docker Compose project with a service `svcdesk` built from
  the repository, `SVCDESK_TEST_CLOCK` set, no host-path bind mounts and no network access after build, and
  MUST answer `GET /health` within 120 seconds of `docker compose up`.
- **FR-016** (R-23): Tickets MUST survive a restart of the service container.

### Conflict Resolutions

Each pair is resolved by rejecting the minimal conflicting part of one requirement; everything else in the pair
is kept and still tested. Full reasoning is in `DECISIONS.md`.

| id | conflicting pair | decision | rejected part | observed by check |
|---|---|---|---|---|
| C1 | R-13 (every SLA clock pauses outside business hours) vs R-14 (P1 around the clock) | `wallclock` | R-13's "does not count against any SLA target" for the two P1 targets | 2.41 (T3: 15:15Z / 19:00Z) |
| C2 | R-09 (a closed ticket is immutable) vs R-10 (reopen a resolved or closed ticket within 7 days) | `immutable` | the words "or closed" in R-10 | 2.35 (409) |
| C3 | R-05 (priority from the matrix and nothing else) vs R-06 (VIP never lower than P2) | `matrix` | R-06 as a whole; the VIP flag is kept as data | 2.46, 2.48 (`P4`) |

### Key Entities

- **Ticket**: id, title, description, reporter (name, e-mail, VIP flag), impact, urgency, computed priority,
  state, `created_at`, `acknowledged_at`, `resolved_at`, `closed_at`, optional `related_to` (id of an earlier
  ticket), SLA block (`ack_due_at`, `resolve_due_at`) fixed at creation.
- **SLA view**: derived per request from a ticket and "now": priority, both due instants, both breach flags,
  paused flag.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: All 49 published conformance checks (CHECKS.md, L1-CORE-2) pass on the running desk.
- **SC-002**: All 8 published SLA vectors reproduce both due instants to the second.
- **SC-003**: The desk is answering health checks within 120 seconds of start, without network access.
- **SC-004**: The Monday lateness report for any ticket needs exactly one request per ticket.
- **SC-005**: The resolutions observed by the checker (C1, C2, C3) equal those declared in `DECISIONS.md`.

## Assumptions

- Public holidays are business days (Polish holidays are out of scope for the course).
- No authentication or roles in Lab 1; "reporter" and "agent" are callers of the same API.
- `related_to` is stored but not validated in Lab 1.
- The desk holds at most a few thousand tickets; no pagination or indexing concerns.
- Error `code` strings (`validation`, `invalid_transition`, `reopen_window_expired`, `ticket_closed`,
  `not_found`) are returned as recommended but are not part of the checked contract.
