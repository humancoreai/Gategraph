"""
WHY: Incidents need a deterministic manual lifecycle for operational use.
INV: State transitions are forward-only and never automatic.
"""

from __future__ import annotations

import sqlite3
from dataclasses import replace
from datetime import datetime, timezone
from typing import Any

from src import operational_hardening

VALID_TRANSITIONS = {
    "open": {"acknowledged"},
    "acknowledged": {"resolved"},
    "resolved": {"archived"},
    "archived": set(),
}


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def transition_incident_state(incident: operational_hardening.IncidentRecord, new_state: str, *, now: str | None = None) -> operational_hardening.IncidentRecord:
    """Return an updated IncidentRecord without mutating the original."""
    if incident.state not in VALID_TRANSITIONS:
        raise ValueError(f"invalid current incident state: {incident.state}")
    if new_state not in VALID_TRANSITIONS[incident.state]:
        raise ValueError(f"invalid incident transition: {incident.state} -> {new_state}")

    timestamp = now or utc_now()
    if new_state == "acknowledged":
        return replace(incident, state=new_state, acknowledged_at=timestamp)
    if new_state == "resolved":
        return replace(incident, state=new_state, resolved_at=timestamp)
    if new_state == "archived":
        return replace(incident, state=new_state)
    raise ValueError(f"invalid incident state: {new_state}")


def validate_incident_transition_history(states: list[str]) -> dict[str, object]:
    """Validate a forward-only incident lifecycle trace without mutating incident state.

    INV: History validation is descriptive and append-only; it never repairs or rewrites incident records.
    """
    if not states:
        return {"ok": False, "reason": "INCIDENT_HISTORY_EMPTY", "violations": []}
    violations: list[dict[str, str]] = []
    for current, nxt in zip(states, states[1:]):
        if current not in VALID_TRANSITIONS:
            violations.append({"from": current, "to": nxt, "reason": "INCIDENT_STATE_UNKNOWN"})
        elif nxt not in VALID_TRANSITIONS[current]:
            violations.append({"from": current, "to": nxt, "reason": "INCIDENT_STATE_REGRESSION_OR_SKIP"})
    final_state = states[-1]
    if final_state not in VALID_TRANSITIONS:
        violations.append({"from": final_state, "to": "", "reason": "INCIDENT_FINAL_STATE_UNKNOWN"})
    return {"ok": not violations, "reason": "INCIDENT_HISTORY_FORWARD_ONLY" if not violations else "INCIDENT_HISTORY_INVALID", "violations": violations}


def transition_incident_state_in_db(conn: sqlite3.Connection, incident_id: str, new_state: str, *, now: str | None = None) -> operational_hardening.IncidentRecord:
    """Persist a manual incident state transition.

    INV: This mutates only operational incident state, never budgets, policies, tokens, or guards.
    """
    operational_hardening.ensure_operational_schema(conn)
    row = conn.execute("SELECT * FROM operational_incidents WHERE incident_id = ?", (incident_id,)).fetchone()
    if row is None:
        raise ValueError(f"incident not found: {incident_id}")

    incident = operational_hardening.incident_from_row(row)
    updated = transition_incident_state(incident, new_state, now=now)

    with conn:
        conn.execute(
            """
            UPDATE operational_incidents
            SET state = ?, acknowledged_at = ?, resolved_at = ?
            WHERE incident_id = ?
            """,
            (updated.state, updated.acknowledged_at, updated.resolved_at, updated.incident_id),
        )
    return updated
