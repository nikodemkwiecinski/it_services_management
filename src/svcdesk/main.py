# ai-generated: 90% - Claude Code drafted, reviewed by me
"""svcdesk HTTP API (API.md sections 1-8)."""

import json
import os
import uuid

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

from . import dora, lifecycle, sla
from .clock import HEADER, InvalidClock, format_instant, parse_instant, request_now
from .priority import compute_priority
from .store import Store
from .validation import ValidationError, validate_create

app = FastAPI(title="svcdesk", docs_url=None, redoc_url=None, openapi_url=None)
store = Store(os.environ.get("SVCDESK_DB", "/data/svcdesk.db"))

ERROR_CODES = {404: "not_found", 405: "method_not_allowed"}


def error(status: int, code: str, message: str) -> JSONResponse:
    return JSONResponse(status_code=status, content={"error": {"code": code, "message": message}})


@app.exception_handler(StarletteHTTPException)
async def http_error(request: Request, exc: StarletteHTTPException) -> JSONResponse:
    return error(exc.status_code, ERROR_CODES.get(exc.status_code, "http_error"), str(exc.detail))


@app.middleware("http")
async def test_clock(request: Request, call_next):
    """Resolve the request's "now" once; a malformed X-Test-Clock is refused before routing."""
    try:
        request.state.now = request_now(request.headers.get(HEADER))
    except InvalidClock as exc:
        return error(422, "invalid_clock", f"{HEADER}: {exc}")
    return await call_next(request)


def ticket_not_found(ticket_id: str) -> JSONResponse:
    return error(404, "not_found", f"ticket {ticket_id} does not exist")


@app.get("/health")
def health() -> dict:
    return {"status": "ok", "service": "svcdesk"}


@app.post("/tickets", status_code=201)
async def create_ticket(request: Request):
    try:
        body = json.loads(await request.body() or b"null")
    except (ValueError, UnicodeDecodeError):
        return error(422, "validation", "request body must be valid JSON")
    try:
        fields = validate_create(body)
    except ValidationError as exc:
        return error(422, "validation", str(exc))

    now = request.state.now
    priority = compute_priority(fields["impact"], fields["urgency"], fields["reporter"]["vip"])
    ack_due, resolve_due = sla.due_instants(priority, now)
    ticket = {
        "id": str(uuid.uuid4()),
        **fields,
        "priority": priority,
        "state": "new",
        "created_at": format_instant(now),
        "acknowledged_at": None,
        "resolved_at": None,
        "closed_at": None,
        "sla": {"ack_due_at": format_instant(ack_due), "resolve_due_at": format_instant(resolve_due)},
    }
    store.insert(ticket)
    return JSONResponse(status_code=201, content=ticket)


@app.get("/tickets")
def list_tickets(state: str | None = None, priority: str | None = None) -> list:
    return [
        ticket
        for ticket in store.all()
        if (state is None or ticket["state"] == state) and (priority is None or ticket["priority"] == priority)
    ]


@app.get("/tickets/{ticket_id}")
def get_ticket(ticket_id: str):
    ticket = store.get(ticket_id)
    return ticket if ticket is not None else ticket_not_found(ticket_id)


@app.get("/tickets/{ticket_id}/sla")
def get_sla(ticket_id: str, request: Request):
    ticket = store.get(ticket_id)
    if ticket is None:
        return ticket_not_found(ticket_id)

    def instant(field: str):
        value = ticket.get(field)
        return parse_instant(value) if value else None

    ack_due_at = parse_instant(ticket["sla"]["ack_due_at"])
    resolve_due_at = parse_instant(ticket["sla"]["resolve_due_at"])
    flags = sla.status(
        priority=ticket["priority"],
        state=ticket["state"],
        ack_due_at=ack_due_at,
        resolve_due_at=resolve_due_at,
        acknowledged_at=instant("acknowledged_at"),
        resolved_at=instant("resolved_at"),
        now=request.state.now,
    )
    return {
        "priority": ticket["priority"],
        "ack_due_at": ticket["sla"]["ack_due_at"],
        "resolve_due_at": ticket["sla"]["resolve_due_at"],
        **flags,
    }


def transition(ticket_id: str, action: str, request: Request):
    try:
        ticket = store.update(ticket_id, lambda t: lifecycle.apply(t, action, request.state.now))
    except lifecycle.TransitionRefused as exc:
        return error(409, exc.code, exc.message)
    return ticket if ticket is not None else ticket_not_found(ticket_id)


@app.post("/tickets/{ticket_id}/ack")
def ack(ticket_id: str, request: Request):
    return transition(ticket_id, "ack", request)


@app.post("/tickets/{ticket_id}/start")
def start(ticket_id: str, request: Request):
    return transition(ticket_id, "start", request)


@app.post("/tickets/{ticket_id}/resolve")
def resolve(ticket_id: str, request: Request):
    return transition(ticket_id, "resolve", request)


@app.post("/tickets/{ticket_id}/close")
def close(ticket_id: str, request: Request):
    return transition(ticket_id, "close", request)


@app.post("/tickets/{ticket_id}/reopen")
def reopen(ticket_id: str, request: Request):
    return transition(ticket_id, "reopen", request)


@app.post("/dora/metrics")
async def dora_metrics(request: Request):
    """Lab 2 METRIC-SPEC.md section 6: a pure function of the request body, nothing is stored."""
    try:
        body = json.loads(await request.body() or b"null")
    except (ValueError, UnicodeDecodeError):
        return error(422, "validation", "request body must be valid JSON")
    try:
        return dora.compute(body)
    except ValidationError as exc:
        return error(422, "validation", str(exc))


@app.get("/dora/ticket-events")
def dora_ticket_events() -> list:
    """Lab 2 METRIC-SPEC.md section 7: every lifecycle instant of every ticket the service holds."""
    return dora.ticket_events(store.all())
