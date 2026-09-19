<!-- ai-generated: 85% - drafted by Claude Code via the speckit-constitution workflow, reviewed by me -->
# svcdesk Constitution

## Core Principles

### I. The Contract Is API.md
The HTTP interface MUST follow `API.md` exactly: paths, field names, status codes, error bodies and the
test clock. Where `REQUIREMENTS.md` and `API.md` differ in precision, `API.md` wins. Every behaviour that
the published checks (`CHECKS.md`) exercise MUST be traceable to a requirement id (R-01..R-25) in the
specification. Rationale: the checker speaks only HTTP; anything outside the contract is untested risk.

### II. Specification Before Code (NON-NEGOTIABLE)
The specification under `specs/` MUST be written, committed, pushed and receipted before any file under
`src/` (other than `src/README.md`) is committed. Plans and tasks MAY follow the receipt; code MUST NOT
precede it. Rationale: Core spec L1-CORE-5 grades the order of commits, and a decision is only a decision
if it is written down before it is built.

### III. Declared Decisions Equal Observed Behaviour
The three conflicting requirement pairs (C1 SLA clock for P1, C2 closed tickets and reopening, C3 VIP
reporters and the priority matrix) MUST each be resolved by rejecting the minimal conflicting part of one
requirement. The value declared in `DECISIONS.md` MUST be exactly what the running service does. A change
of decision MUST change the specification, `DECISIONS.md` and the code in the same commit.

### IV. Deterministic Time
All instants MUST be RFC 3339, stored and returned in UTC with a `Z` suffix. "Now" MUST come from the
per-request `X-Test-Clock` header when `SVCDESK_TEST_CLOCK` is `1` or `true`, otherwise from real UTC
time; the service MUST NOT compare clocks across requests or enforce monotonic time. Business hours MUST
be computed in `Europe/Warsaw` from the IANA time zone database, never from a fixed offset. Rationale:
SLA arithmetic is the core value of the desk and must be reproducible from the published vectors T1..T8.

### V. Self-Contained and Simple
The service MUST run without network access once its image is built: every dependency is installed at
build time. Persistence MUST use a named volume, never a host-path bind mount. The implementation SHOULD
use the smallest set of dependencies that satisfies the contract (standard library first).
Rationale: the grading sandbox has no egress and resolves no host paths.

## Technology and Deployment Constraints

- Language and runtime: Python 3.13, FastAPI served by uvicorn on port 8080 inside the container.
- Storage: SQLite in `/data` on the named volume `svcdesk-data`, so tickets survive a container restart.
- Delivery: a Docker Compose project at the repository root with a service named `svcdesk` that has a
  `build:` key and sets `SVCDESK_TEST_CLOCK: "1"`; `GET /health` answers within 120 s of `up`.
- Every file under `src/` and `specs/` with a checked extension, and `DECISIONS.md`, MUST carry an
  `ai-generated: <0-100>% - <how>` comment in its first ten lines.
- No personal data (hostnames, usernames, diagnostic output) is committed to the repository.

## Development Workflow and Quality Gates

1. Specify (this constitution, then `specs/<nnn>-<feature>/spec.md`), commit, push, obtain the `specs`
   receipt.
2. Record the decisions in `DECISIONS.md`, then plan and tasks, then implement.
3. Before any submission, `itsmlab verify 1` MUST exit 0 with every Core spec passing on the committed
   tree (not `(dirty)`), and its `observations` line MUST equal the front matter of `DECISIONS.md`.
4. Submissions are immutable tags `lab1/vN`; a pushed tag is never moved or deleted.

## Governance

This constitution governs every specification, plan, task and line of code in this repository; where a
tool default conflicts with it, the constitution wins. Amendments are made by editing this file in a
dedicated commit that states the reason, and any specification or code affected by the amendment is
updated in the same change. Versioning follows semantic versioning: MAJOR for removing or redefining a
principle, MINOR for adding one or materially expanding guidance, PATCH for wording. Every plan produced
by `/speckit-plan` MUST include a constitution check against principles I-V.

**Version**: 1.0.0 | **Ratified**: 2026-09-19 | **Last Amended**: 2026-09-19
