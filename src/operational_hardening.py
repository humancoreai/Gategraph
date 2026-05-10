"""
WHY: Operational hardening makes the existing governance state inspectable without adding autonomy.
INV: This module observes, replays, and records incidents; it never allows actions or mutates core policy.
SEC: Any inconsistency is reported as fail-closed evidence, not repaired silently.
"""

from __future__ import annotations

import json
import sqlite3
import uuid
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from typing import Any

from src import budget_ledger

SCHEMA_VERSION = "0.8.27"
INCIDENT_STATES = ("open", "acknowledged", "resolved", "archived")
INCIDENT_SEVERITIES = ("low", "medium", "high", "critical")


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


@dataclass(frozen=True)
class BudgetScopeSnapshot:
    scope_id: str
    scope_type: str
    parent_scope_id: str | None
    allocated_units: int
    consumed_units: int
    reserved_units: int
    available_units: int
    usage_ratio: float
    state: str
    reason_code: str


@dataclass(frozen=True)
class BudgetSnapshot:
    schema_version: str
    generated_at: str
    scopes: list[BudgetScopeSnapshot]
    totals_by_type: dict[str, dict[str, int]]
    escalation_counts: dict[str, int]
    anomalies: list[str] = field(default_factory=list)


@dataclass(frozen=True)
class AuditReplayReport:
    schema_version: str
    generated_at: str
    ok: bool
    checked_events: int
    checked_decisions: int
    checked_tokens: int
    checked_budget_scopes: int
    violations: list[str] = field(default_factory=list)


@dataclass(frozen=True)
class IncidentRecord:
    incident_id: str
    severity: str
    trigger_type: str
    trigger_ref: str
    state: str
    reason_code: str
    details: dict[str, Any]
    created_at: str
    acknowledged_at: str | None = None
    resolved_at: str | None = None



@dataclass(frozen=True)
class OperationalAlert:
    alert_id: str
    severity: str
    reason_code: str
    trigger_type: str
    trigger_ref: str
    message: str
    created_at: str


ALERT_PRIORITY = {"critical": 4, "high": 3, "medium": 2, "low": 1}


def evaluate_operational_alerts(incidents: list[IncidentRecord]) -> list[OperationalAlert]:
    """WHY: alerts make operational findings visible without becoming an action path.
    INV: alert evaluation is pure/read-only; it never acknowledges, resolves, or repairs incidents.
    """
    alerts: list[OperationalAlert] = []
    for incident in incidents:
        severity = incident.severity if incident.severity in INCIDENT_SEVERITIES else "critical"
        alerts.append(OperationalAlert(
            alert_id=f"ALERT-{incident.incident_id}",
            severity=severity,
            reason_code=incident.reason_code,
            trigger_type=incident.trigger_type,
            trigger_ref=incident.trigger_ref,
            message=_alert_message(incident),
            created_at=utc_now(),
        ))
    return sorted(alerts, key=lambda a: (-ALERT_PRIORITY.get(a.severity, 4), a.created_at, a.reason_code, a.trigger_ref))


def evaluate_open_operational_alerts(conn: sqlite3.Connection) -> list[OperationalAlert]:
    """WHY: callers can inspect open operational risk without mutating core governance state."""
    return evaluate_operational_alerts(list_open_incidents(conn))


def _alert_message(incident: IncidentRecord) -> str:
    if incident.reason_code == "OPERATIONAL_AUDIT_INCONSISTENCY":
        return "Audit replay detected an operational consistency violation."
    if incident.reason_code == "OPERATIONAL_BUDGET_ANOMALY":
        return "Budget snapshot detected a ledger anomaly."
    if incident.reason_code == "OPERATIONAL_SCOPE_BLOCKED":
        return "Budget scope is blocked and requires human review."
    return "Operational incident requires human review."

def ensure_operational_schema(conn: sqlite3.Connection) -> None:
    """INV: Incident records are append-only operational evidence, not recovery commands."""
    conn.executescript(
        """
        CREATE TABLE IF NOT EXISTS operational_incidents (
            incident_id TEXT PRIMARY KEY,
            schema_version TEXT NOT NULL,
            severity TEXT NOT NULL CHECK (severity IN ('low','medium','high','critical')),
            trigger_type TEXT NOT NULL,
            trigger_ref TEXT NOT NULL,
            state TEXT NOT NULL CHECK (state IN ('open','acknowledged','resolved','archived')),
            reason_code TEXT NOT NULL,
            details_json TEXT NOT NULL,
            created_at TEXT NOT NULL,
            acknowledged_at TEXT,
            resolved_at TEXT
        );

        CREATE UNIQUE INDEX IF NOT EXISTS idx_operational_incidents_trigger
            ON operational_incidents(trigger_type, trigger_ref, reason_code);
        CREATE INDEX IF NOT EXISTS idx_operational_incidents_state
            ON operational_incidents(state, severity);
        """
    )
    columns = {row["name"] if isinstance(row, sqlite3.Row) else row[1] for row in conn.execute("PRAGMA table_info(operational_incidents)").fetchall()}
    if "acknowledged_at" not in columns:
        conn.execute("ALTER TABLE operational_incidents ADD COLUMN acknowledged_at TEXT")
    if "resolved_at" not in columns:
        conn.execute("ALTER TABLE operational_incidents ADD COLUMN resolved_at TEXT")


def _rows(conn: sqlite3.Connection, query: str, params: tuple[Any, ...] = ()) -> list[sqlite3.Row]:
    return list(conn.execute(query, params).fetchall())


def collect_budget_snapshot(conn: sqlite3.Connection) -> BudgetSnapshot:
    """WHY: snapshot exposes the ledger state without consuming or reserving budget."""
    budget_ledger.ensure_budget_schema(conn)
    rows = _rows(conn, "SELECT * FROM budget_scopes ORDER BY scope_type, scope_id")
    scopes: list[BudgetScopeSnapshot] = []
    totals_by_type: dict[str, dict[str, int]] = {}
    escalation_counts = {state: 0 for state in budget_ledger.ESCALATION_ORDER}
    anomalies: list[str] = []

    for row in rows:
        allocated = int(row["allocated_units"])
        consumed = int(row["consumed_units"])
        reserved = int(row["reserved_units"])
        available = max(allocated - consumed - reserved, 0)
        usage_ratio = 1.0 if allocated <= 0 and (consumed or reserved) else ((consumed + reserved) / allocated if allocated else 0.0)
        state = str(row["state"])
        expected_state = budget_ledger.derive_escalation_state(consumed, reserved, allocated)
        if state != expected_state:
            anomalies.append(f"BUDGET_STATE_DRIFT:{row['scope_id']}:{state}!={expected_state}")
        if consumed + reserved > allocated:
            anomalies.append(f"BUDGET_OVERSPEND:{row['scope_id']}")
        if state not in escalation_counts:
            anomalies.append(f"UNKNOWN_ESCALATION_STATE:{row['scope_id']}:{state}")
        else:
            escalation_counts[state] += 1

        scope_type = str(row["scope_type"])
        totals = totals_by_type.setdefault(scope_type, {"allocated": 0, "consumed": 0, "reserved": 0, "available": 0})
        totals["allocated"] += allocated
        totals["consumed"] += consumed
        totals["reserved"] += reserved
        totals["available"] += available
        scopes.append(BudgetScopeSnapshot(
            scope_id=str(row["scope_id"]),
            scope_type=scope_type,
            parent_scope_id=row["parent_scope_id"],
            allocated_units=allocated,
            consumed_units=consumed,
            reserved_units=reserved,
            available_units=available,
            usage_ratio=round(usage_ratio, 4),
            state=state,
            reason_code=str(row["reason_code"]),
        ))

    return BudgetSnapshot(SCHEMA_VERSION, utc_now(), scopes, totals_by_type, escalation_counts, anomalies)


def replay_audit_consistency(conn: sqlite3.Connection) -> AuditReplayReport:
    """INV: replay only checks relationships; it never rewrites audit history."""
    budget_ledger.ensure_budget_schema(conn)
    violations: list[str] = []

    events = _rows(conn, "SELECT event_id FROM events")
    decisions = _rows(conn, "SELECT decision_id, event_id, task_id FROM decisions")
    tokens = _rows(conn, "SELECT token_id, decision_id, task_id, budget_scope_id, budget_reservation_id FROM capability_tokens")
    scopes = _rows(conn, "SELECT scope_id, allocated_units, consumed_units, reserved_units, state FROM budget_scopes")

    event_ids = {r["event_id"] for r in events}
    decision_ids = {r["decision_id"] for r in decisions}
    scope_ids = {r["scope_id"] for r in scopes}
    reservation_ids = {r["reservation_id"] for r in _rows(conn, "SELECT reservation_id FROM budget_reservations")}

    for decision in decisions:
        if decision["event_id"] not in event_ids:
            violations.append(f"DECISION_EVENT_MISSING:{decision['decision_id']}->{decision['event_id']}")

    for token in tokens:
        if token["decision_id"] not in decision_ids:
            violations.append(f"TOKEN_DECISION_MISSING:{token['token_id']}->{token['decision_id']}")
        if token["budget_scope_id"] and token["budget_scope_id"] not in scope_ids:
            violations.append(f"TOKEN_SCOPE_MISSING:{token['token_id']}->{token['budget_scope_id']}")
        if token["budget_reservation_id"] and token["budget_reservation_id"] not in reservation_ids:
            violations.append(f"TOKEN_RESERVATION_MISSING:{token['token_id']}->{token['budget_reservation_id']}")

    for scope in scopes:
        allocated = int(scope["allocated_units"])
        consumed = int(scope["consumed_units"])
        reserved = int(scope["reserved_units"])
        expected_state = budget_ledger.derive_escalation_state(consumed, reserved, allocated)
        if consumed + reserved > allocated:
            violations.append(f"BUDGET_OVERSPEND:{scope['scope_id']}")
        if scope["state"] != expected_state:
            violations.append(f"BUDGET_STATE_DRIFT:{scope['scope_id']}:{scope['state']}!={expected_state}")

    return AuditReplayReport(
        SCHEMA_VERSION,
        utc_now(),
        ok=not violations,
        checked_events=len(events),
        checked_decisions=len(decisions),
        checked_tokens=len(tokens),
        checked_budget_scopes=len(scopes),
        violations=violations,
    )


def incident_from_row(row: sqlite3.Row) -> IncidentRecord:
    return IncidentRecord(
        incident_id=row["incident_id"],
        severity=row["severity"],
        trigger_type=row["trigger_type"],
        trigger_ref=row["trigger_ref"],
        state=row["state"],
        reason_code=row["reason_code"],
        details=json.loads(row["details_json"]),
        created_at=row["created_at"],
        acknowledged_at=row["acknowledged_at"],
        resolved_at=row["resolved_at"],
    )


def _insert_incident(conn: sqlite3.Connection, *, severity: str, trigger_type: str, trigger_ref: str, reason_code: str, details: dict[str, Any]) -> IncidentRecord:
    if severity not in INCIDENT_SEVERITIES:
        severity = "critical"
    incident_id = f"INC-{uuid.uuid4().hex[:12].upper()}"
    created_at = utc_now()
    conn.execute(
        """
        INSERT OR IGNORE INTO operational_incidents
          (incident_id, schema_version, severity, trigger_type, trigger_ref, state, reason_code, details_json, created_at)
        VALUES (?, ?, ?, ?, ?, 'open', ?, ?, ?)
        """,
        (incident_id, SCHEMA_VERSION, severity, trigger_type, trigger_ref, reason_code, json.dumps(details, sort_keys=True), created_at),
    )
    row = conn.execute(
        """SELECT * FROM operational_incidents
           WHERE trigger_type = ? AND trigger_ref = ? AND reason_code = ?
           ORDER BY created_at ASC LIMIT 1""",
        (trigger_type, trigger_ref, reason_code),
    ).fetchone()
    return incident_from_row(row)


def detect_operational_incidents(conn: sqlite3.Connection) -> list[IncidentRecord]:
    """SEC: detection records incidents but does not unblock, retry, or approve anything."""
    ensure_operational_schema(conn)
    snapshot = collect_budget_snapshot(conn)
    replay = replay_audit_consistency(conn)
    incidents: list[IncidentRecord] = []

    with conn:
        for anomaly in snapshot.anomalies:
            incidents.append(_insert_incident(
                conn, severity="high", trigger_type="budget_snapshot", trigger_ref=anomaly,
                reason_code="OPERATIONAL_BUDGET_ANOMALY", details={"anomaly": anomaly},
            ))
        for violation in replay.violations:
            incidents.append(_insert_incident(
                conn, severity="critical", trigger_type="audit_replay", trigger_ref=violation,
                reason_code="OPERATIONAL_AUDIT_INCONSISTENCY", details={"violation": violation},
            ))
        for scope in snapshot.scopes:
            if scope.state == "blocked":
                incidents.append(_insert_incident(
                    conn, severity="high", trigger_type="budget_scope", trigger_ref=scope.scope_id,
                    reason_code="OPERATIONAL_SCOPE_BLOCKED", details=asdict(scope),
                ))

    return incidents


def list_open_incidents(conn: sqlite3.Connection) -> list[IncidentRecord]:
    ensure_operational_schema(conn)
    rows = _rows(conn, "SELECT * FROM operational_incidents WHERE state = 'open' ORDER BY severity DESC, created_at ASC")
    return [incident_from_row(r) for r in rows]
