# ai-generated: 90% - Claude Code drafted, reviewed by me
"""SQLite persistence (R-23): one row per ticket, the ticket document stored as JSON."""

import json
import os
import sqlite3
import threading
from contextlib import contextmanager
from typing import Callable, Iterator


class Store:
    def __init__(self, path: str) -> None:
        directory = os.path.dirname(path)
        if directory:
            os.makedirs(directory, exist_ok=True)
        self._conn = sqlite3.connect(path, check_same_thread=False, isolation_level=None)
        self._conn.execute("PRAGMA journal_mode=WAL")
        self._conn.execute("CREATE TABLE IF NOT EXISTS tickets (id TEXT PRIMARY KEY, doc TEXT NOT NULL)")
        # One lock for every access keeps read-modify-write transitions atomic across worker threads.
        self._lock = threading.Lock()

    @contextmanager
    def _locked(self) -> Iterator[sqlite3.Connection]:
        with self._lock:
            yield self._conn

    def insert(self, ticket: dict) -> None:
        with self._locked() as conn:
            conn.execute("INSERT INTO tickets (id, doc) VALUES (?, ?)", (ticket["id"], json.dumps(ticket)))

    def get(self, ticket_id: str) -> dict | None:
        with self._locked() as conn:
            row = conn.execute("SELECT doc FROM tickets WHERE id = ?", (ticket_id,)).fetchone()
        return json.loads(row[0]) if row else None

    def all(self) -> list[dict]:
        with self._locked() as conn:
            rows = conn.execute("SELECT doc FROM tickets").fetchall()
        return [json.loads(row[0]) for row in rows]

    def update(self, ticket_id: str, change: Callable[[dict], dict]) -> dict | None:
        """Apply `change` to the stored ticket under the lock; `change` may raise to abort."""
        with self._locked() as conn:
            row = conn.execute("SELECT doc FROM tickets WHERE id = ?", (ticket_id,)).fetchone()
            if row is None:
                return None
            ticket = change(json.loads(row[0]))
            conn.execute("UPDATE tickets SET doc = ? WHERE id = ?", (json.dumps(ticket), ticket_id))
            return ticket
