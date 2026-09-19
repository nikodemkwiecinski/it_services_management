<!-- ai-generated: 90% - drafted by Claude Code via the speckit-plan workflow (Phase 1), reviewed by me -->
# Quickstart: run and validate svcdesk

## Prerequisites

Docker with Compose v2; PowerShell on Windows (`.\itsmlab.ps1`) or bash (`./itsmlab.sh`).

## Run

```powershell
docker compose up --build --wait svcdesk
Invoke-RestMethod http://localhost:8080/health          # {"status":"ok","service":"svcdesk"}
```

## Validate by hand

```powershell
$h = @{ 'X-Test-Clock' = '2026-10-16T15:00:00Z' }       # T3: P1 on Friday 17:00 CEST
$b = '{"title":"Network down","reporter":{"name":"Desk"},"impact":1,"urgency":1}'
$t = Invoke-RestMethod -Method Post http://localhost:8080/tickets -Headers $h -ContentType application/json -Body $b
$t.sla                                                  # ack 2026-10-16T15:15:00Z, resolve 2026-10-16T19:00:00Z (C1 = wallclock)
```

Expected: the T1..T8 business-hours columns of API.md section 4 for P2..P4 and the wall-clock columns for P1;
`GET /tickets/{id}/sla` breach and pause as in API.md section 5; reopen on a closed ticket answers 409.

## Validate with the checker

```powershell
.\itsmlab.ps1 verify 1
```

Expected: every Core spec `pass` except L1-CORE-5 `skip`, and the last line
`observations  C1=wallclock  C2=immutable  C3=matrix`, equal to the front matter of `DECISIONS.md`.

## Stop

```powershell
docker compose down          # keeps the named volume; add -v to delete the stored tickets
```
