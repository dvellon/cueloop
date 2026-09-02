"""Bounded local event/feedback persistence with no raw-audio fields."""

from __future__ import annotations

from pathlib import Path
import sqlite3
from threading import RLock

from .engine import EventRecord


EVENT_COLUMNS = (
    "id",
    "class_name",
    "confidence",
    "detected_at",
    "pod_id",
    "location",
    "priority",
    "decision_state",
    "evidence_windows",
    "evidence_tier",
    "packet_loss_rate",
    "pipeline_latency_ms",
    "user_action",
)


class EventStore:
    def __init__(self, path: str = ":memory:", *, maximum_events: int = 500) -> None:
        if maximum_events < 1:
            raise ValueError("maximum_events must be positive")
        self.path = path
        self.maximum_events = maximum_events
        if path != ":memory:":
            Path(path).parent.mkdir(parents=True, exist_ok=True)
        self._connection = sqlite3.connect(path, check_same_thread=False)
        self._connection.row_factory = sqlite3.Row
        self._lock = RLock()
        self._initialize()

    def _initialize(self) -> None:
        with self._lock, self._connection:
            self._connection.executescript(
                """
                PRAGMA journal_mode=WAL;
                PRAGMA foreign_keys=ON;
                CREATE TABLE IF NOT EXISTS events (
                    id TEXT PRIMARY KEY,
                    class_name TEXT NOT NULL,
                    confidence REAL NOT NULL CHECK(confidence BETWEEN 0 AND 1),
                    detected_at TEXT NOT NULL,
                    pod_id INTEGER NOT NULL,
                    location TEXT NOT NULL,
                    priority INTEGER NOT NULL CHECK(priority BETWEEN 1 AND 3),
                    decision_state TEXT NOT NULL CHECK(decision_state = 'confirmed'),
                    evidence_windows INTEGER NOT NULL CHECK(evidence_windows >= 2),
                    evidence_tier TEXT NOT NULL,
                    packet_loss_rate REAL NOT NULL CHECK(packet_loss_rate BETWEEN 0 AND 1),
                    pipeline_latency_ms REAL,
                    user_action TEXT NOT NULL DEFAULT 'pending'
                        CHECK(user_action IN ('pending', 'acknowledged', 'dismissed'))
                );
                CREATE TABLE IF NOT EXISTS feedback (
                    event_id TEXT PRIMARY KEY REFERENCES events(id) ON DELETE CASCADE,
                    action TEXT NOT NULL CHECK(action IN ('acknowledged', 'dismissed')),
                    recorded_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
                );
                """
            )

    def add(self, event: EventRecord) -> None:
        values = event.as_dict()
        if set(values) != set(EVENT_COLUMNS):
            raise ValueError("event schema mismatch; audio payloads are never accepted")
        with self._lock, self._connection:
            self._connection.execute(
                f"INSERT INTO events ({', '.join(EVENT_COLUMNS)}) "
                f"VALUES ({', '.join('?' for _ in EVENT_COLUMNS)})",
                tuple(values[column] for column in EVENT_COLUMNS),
            )
            self._connection.execute(
                """
                DELETE FROM events
                WHERE id IN (
                    SELECT id FROM events
                    ORDER BY detected_at DESC
                    LIMIT -1 OFFSET ?
                )
                """,
                (self.maximum_events,),
            )

    def list(self, *, limit: int = 50) -> list[dict[str, object]]:
        bounded_limit = max(1, min(int(limit), 500))
        with self._lock:
            rows = self._connection.execute(
                "SELECT * FROM events ORDER BY detected_at DESC LIMIT ?",
                (bounded_limit,),
            ).fetchall()
        return [dict(row) for row in rows]

    def set_action(self, event_id: str, action: str) -> bool:
        if action not in ("acknowledged", "dismissed"):
            raise ValueError("unsupported feedback action")
        with self._lock, self._connection:
            cursor = self._connection.execute(
                "UPDATE events SET user_action = ? WHERE id = ?",
                (action, event_id),
            )
            if cursor.rowcount:
                self._connection.execute(
                    """
                    INSERT INTO feedback(event_id, action) VALUES (?, ?)
                    ON CONFLICT(event_id) DO UPDATE SET
                        action = excluded.action,
                        recorded_at = CURRENT_TIMESTAMP
                    """,
                    (event_id, action),
                )
            return cursor.rowcount > 0

    def clear(self) -> None:
        with self._lock, self._connection:
            self._connection.execute("DELETE FROM events")

    def close(self) -> None:
        with self._lock:
            self._connection.close()
