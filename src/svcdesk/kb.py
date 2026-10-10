# ai-generated: 90% - Claude Code drafted, reviewed by me
"""GET /kb/search's call to the upstream index kb-index (Lab 3 MONITORING-SPEC.md M-02)."""

import os
from urllib.parse import quote

import httpx

KB_INDEX_URL = os.environ.get("KB_INDEX_URL", "http://kb-index:8080").rstrip("/")
MAX_QUERY_LENGTH = 200

# At least 2 s (M-02). No retries and no cache: exactly one upstream call per valid request.
_client = httpx.AsyncClient(timeout=httpx.Timeout(5.0), limits=httpx.Limits(max_connections=200))


class UpstreamUnavailable(Exception):
    """kb-index answered non-200, timed out, could not be reached, or answered something that is not its JSON."""


def query_error(q: str | None) -> str | None:
    """Why `q` is refused, or None when it is valid."""
    if q is None:
        return "query parameter q is required"
    if not 1 <= len(q) <= MAX_QUERY_LENGTH:
        return f"q must be 1 to {MAX_QUERY_LENGTH} characters"
    return None


async def search(q: str) -> list:
    """The upstream's hits for `q`, unchanged."""
    try:
        response = await _client.get(f"{KB_INDEX_URL}/search?q={quote(q, safe='')}")
    except httpx.HTTPError as exc:
        raise UpstreamUnavailable(f"kb-index could not be reached: {type(exc).__name__}") from exc
    if response.status_code != 200:
        raise UpstreamUnavailable(f"kb-index answered {response.status_code}")
    try:
        return response.json()["hits"]
    except (ValueError, KeyError, TypeError) as exc:
        raise UpstreamUnavailable("kb-index answered without hits") from exc
