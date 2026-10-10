# ai-generated: 90% - Claude Code drafted, reviewed by me
"""The request histogram and GET /metrics (Lab 3 MONITORING-SPEC.md M-03 to M-07)."""

import time

from prometheus_client import CollectorRegistry, Histogram, disable_created_metrics, generate_latest
from starlette.routing import Match

# Prometheus text exposition format 0.0.4 (M-03); Prometheus 3 refuses any other Content-Type.
CONTENT_TYPE = "text/plain; version=0.0.4; charset=utf-8"
UNMATCHED = "unmatched"

# The ladder, in seconds, at most 30 finite boundaries (M-06), designed from the measured p99 (149 ms on
# 10 October 2026, slow mode 110 to 220 ms; slo.md "Buckets"): 5 to 10 ms steps from 0.1 to 0.2 s resolve any q in
# (0.1, 0.2] (M-11), 0.25 is the latency SLI's threshold (M-13), the rest is coarse cover up to the 5 s timeout.
BUCKETS = (
    0.005, 0.01, 0.02, 0.03, 0.04, 0.05, 0.075, 0.1,
    0.11, 0.12, 0.13, 0.135, 0.14, 0.145, 0.15, 0.155, 0.16, 0.165, 0.17, 0.18, 0.19, 0.2,
    0.25, 0.3, 0.5, 1.0, 2.0, 2.5, 5.0,
)

# An own registry and no `_created` series: /metrics exposes the histogram and nothing else, so every new label
# set costs as few series as possible (M-07).
disable_created_metrics()
registry = CollectorRegistry()
REQUEST_DURATION = Histogram(
    "http_server_request_duration_seconds",
    "Duration of HTTP server requests, in seconds.",
    ["http_request_method", "http_route", "http_response_status_code"],
    buckets=BUCKETS,
    registry=registry,
)


def exposition() -> bytes:
    return generate_latest(registry)


def route_template(app, scope) -> str:
    """The template of the matched route (M-05), never the raw path; one constant for no route at all."""
    route = scope.get("route")
    if route is None:
        # Answered before routing (an invalid X-Test-Clock) or refused by the router (405): match it ourselves.
        for candidate in app.router.routes:
            match, _ = candidate.matches(scope)
            if match is not Match.NONE:
                route = candidate
                break
    return getattr(route, "path", None) or UNMATCHED


class RequestDurationMiddleware:
    """Pure ASGI middleware, outermost: observes every answered request exactly once (M-04), /metrics excepted."""

    def __init__(self, app, *, skip_paths=("/metrics",)) -> None:
        self.app = app
        self.skip_paths = skip_paths

    async def __call__(self, scope, receive, send) -> None:
        if scope["type"] != "http" or scope["path"] in self.skip_paths:
            await self.app(scope, receive, send)
            return

        start = time.perf_counter()
        status = 500

        async def send_and_record_status(message) -> None:
            nonlocal status
            if message["type"] == "http.response.start":
                status = message["status"]
            await send(message)

        try:
            await self.app(scope, receive, send_and_record_status)
        finally:
            REQUEST_DURATION.labels(
                http_request_method=scope["method"],
                http_route=route_template(scope["app"], scope),
                http_response_status_code=str(status),
            ).observe(time.perf_counter() - start)
