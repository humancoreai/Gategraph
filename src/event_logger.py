"""
INV: events are never updated or deleted — this module only inserts or returns existing records.
SEC: idempotency_key uniqueness is enforced by DB unique index and application logic.
WHY: idempotent logging allows safe retries without audit corruption.
"""

import json
import sqlite3
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any, Dict, Optional

SCHEMA_VERSION = "0.4"
ACTOR_LAYER = "governance"
ACTOR_VERSION = "0.4.0"


@dataclass(frozen=True)
class EventRecord:
    event_id: str
    idempotency_key: str
    was_duplicate: bool


def log_event(
    conn: sqlite3.Connection,
    *,
    event_id: str,
    idempotency_key: str,
    correlation_id: str,
    causation_id: Optional[str],
    event_type: str,
    task_id: str,
    actor_component: str,
    input_data: Dict[str, Any],
    evaluation: Dict[str, Any],
    decision: Dict[str, Any],
) -> EventRecord:
    existing = conn.execute(
        "SELECT event_id, idempotency_key FROM events WHERE idempotency_key = ?",
        (idempotency_key,),
    ).fetchone()
    if existing:
        return EventRecord(existing["event_id"], existing["idempotency_key"], True)

    now = datetime.now(timezone.utc).isoformat()
    conn.execute(
        """
        INSERT INTO events (
            event_id, schema_version, idempotency_key, correlation_id, causation_id,
            type, timestamp, task_id, actor_layer, actor_component, actor_version,
            input_json, evaluation_json, decision_json
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            event_id, SCHEMA_VERSION, idempotency_key, correlation_id, causation_id,
            event_type, now, task_id, ACTOR_LAYER, actor_component, ACTOR_VERSION,
            json.dumps(input_data), json.dumps(evaluation), json.dumps(decision),
        ),
    )
    return EventRecord(event_id, idempotency_key, False)


def log_relation(conn: sqlite3.Connection, subject_id: str, subject_type: str, relation: str, object_id: str, object_type: str) -> None:
    now = datetime.now(timezone.utc).isoformat()
    conn.execute(
        """
        INSERT INTO relations (subject_id, subject_type, relation, object_id, object_type, created_at)
        VALUES (?, ?, ?, ?, ?, ?)
        """,
        (subject_id, subject_type, relation, object_id, object_type, now),
    )


def count_events(conn: sqlite3.Connection) -> int:
    return conn.execute("SELECT COUNT(*) FROM events").fetchone()[0]
