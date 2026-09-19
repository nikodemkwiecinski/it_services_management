<!-- ai-generated: 85% - drafted by Claude Code via the speckit-plan workflow (Phase 0), reviewed by me -->
# Research: svcdesk ticketing API

No item in the Technical Context was left as NEEDS CLARIFICATION; this file records the decisions and why.

## Web framework

- **Decision**: FastAPI 0.141.1 on uvicorn 0.52.4, handlers taking the raw `Request`.
- **Rationale**: matches `Dockerfile.example` (`svcdesk.main:app`), gives exception handlers for unknown paths
  and methods so every error is a JSON `{"error": {...}}` body. Reading the raw body avoids Pydantic's lax
  coercion (`"2"` to `2`) and its `{"detail": ...}` error shape, both of which contradict API.md section 7.
- **Alternatives considered**: standard library `http.server` (no dependencies, but hand-written routing and
  threading); Pydantic strict models (still need custom error mapping, more code than the validator itself).

## Business-hours arithmetic

- **Decision**: convert `created_at` to Europe/Warsaw, work in naive local time, move to the next opening,
  consume the target from consecutive [08:00, 16:00) windows on Monday to Friday, and finish in the current
  window when `remaining <= time left until 16:00` (so a target ending exactly at closing is due at 16:00, the
  tie rule); attach Europe/Warsaw to the result and convert to UTC.
- **Rationale**: DST transitions happen on Sunday at night, never inside a business window, so local wall time
  inside a window is unambiguous and the offset is resolved once at the end. Reproduces T1..T8 (T8 crosses the
  end of DST, T5 is in CET).
- **Alternatives considered**: minute-by-minute stepping (slow for 72 h targets, same result); fixed UTC+1/+2
  offsets (wrong across DST, violates constitution principle IV).

## Test clock parsing

- **Decision**: accept only RFC 3339 date-time with seconds and an explicit offset
  (`YYYY-MM-DDTHH:MM:SS[.frac](Z|±HH:MM)`), checked by a regular expression, then parsed with
  `datetime.fromisoformat`; anything else is 422 `invalid_clock`. Parsed on every request by a middleware
  when `SVCDESK_TEST_CLOCK` is `1` or `true`.
- **Rationale**: API.md section 8 says a naive timestamp is malformed; `fromisoformat` alone accepts dates
  without time and naive values.

## Persistence

- **Decision**: SQLite file on the named volume, one table `tickets(id TEXT PRIMARY KEY, doc TEXT)`, the
  ticket JSON in `doc`; one connection guarded by a lock so read-modify-write transitions are atomic.
- **Rationale**: R-23 needs restart survival; the ticket document is small and always read whole; filters run
  in memory (at most a few thousand tickets).
- **Alternatives considered**: in-memory dict (fails R-23); a column per field (more code, no benefit in Lab 1).

## Identifiers and instants

- **Decision**: UUID4 ids; instants formatted as `YYYY-MM-DDTHH:MM:SSZ` in UTC, with fractional seconds only
  when present.
- **Rationale**: R-17, R-18; the checker compares instants, not strings, and sends whole seconds.
