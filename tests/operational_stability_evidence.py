"""
WHY: Evidence for v0.8.30 proves Operational Stability A-D without adding autonomous recovery.
INV: A-C are read-only; D blocks only through deterministic Governance/Flood Guard limits.
"""
from __future__ import annotations

import sqlite3
import sys
from dataclasses import asdict
from pathlib import Path
from datetime import datetime, timezone, timedelta

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from src.database import init_db, get_connection
from src import (
    alert_aggregator,
    flood_guard,
    guard_orchestrator,
    incident_state_manager,
    monitoring_export,
    operational_hardening,
    runtime_guard,
    session_budget_guard,
)


def fresh_conn(name: str) -> sqlite3.Connection:
    db_path = PROJECT_ROOT / "tests" / "logs" / f"{name}.db"
    db_path.parent.mkdir(parents=True, exist_ok=True)
    if db_path.exists():
        db_path.unlink()
    init_db(db_path)
    return get_connection(db_path)


def check(name: str, condition: bool, detail: dict) -> tuple[bool, str, dict]:
    status = "✓" if condition else "✗"
    print(f"{status} {name}: {detail}")
    return condition, name, detail


def make_incident(incident_id: str, severity: str = "high", state: str = "open") -> operational_hardening.IncidentRecord:
    return operational_hardening.IncidentRecord(
        incident_id=incident_id,
        severity=severity,
        trigger_type="budget_snapshot",
        trigger_ref="BUDGET_OVERSPEND:actor:x",
        state=state,
        reason_code="OPERATIONAL_BUDGET_ANOMALY",
        details={"fixture": True},
        created_at="2026-04-28T00:00:00+00:00",
    )


def insert_session_decision(conn: sqlite3.Connection, *, actor_id: str, cost: int, created_at: datetime, decision: str = "continue") -> None:
    session_budget_guard.ensure_session_budget_schema(conn)
    conn.execute(
        """
        INSERT INTO session_budget_decisions (
            decision_id, session_id, task_id, actor_id, projected_cost_units,
            decision, reason, created_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (f"SBD-{actor_id}-{created_at.timestamp()}-{cost}", "SES-FLOOD", f"TASK-{created_at.timestamp()}", actor_id, cost, decision, "fixture", created_at.isoformat()),
    )
    conn.commit()


def main() -> int:
    checks: list[tuple[bool, str, dict]] = []

    # A: Alert Aggregator
    alerts = [
        {"alert_id": "a1", "severity": "high", "reason_code": "R1", "trigger_type": "audit", "trigger_ref": "x", "created_at": "2026-04-28T00:00:01+00:00"},
        {"alert_id": "a2", "severity": "critical", "reason_code": "R1", "trigger_type": "audit", "trigger_ref": "x", "created_at": "2026-04-28T00:00:02+00:00"},
        {"alert_id": "a3", "severity": "low", "reason_code": "R1", "trigger_type": "audit", "trigger_ref": "y", "created_at": "2026-04-28T00:00:03+00:00"},
    ]
    aggregated = alert_aggregator.aggregate_alerts(alerts)
    same = next(a for a in aggregated if a["trigger_ref"] == "x")
    checks.append(check(
        "alert_aggregator_groups_exact_cause_and_keeps_highest_severity",
        len(aggregated) == 2 and same["count"] == 2 and same["severity"] == "critical",
        {"aggregated": aggregated},
    ))

    # B: Incident State Manager
    inc = make_incident("INC-A")
    ack = incident_state_manager.transition_incident_state(inc, "acknowledged", now="2026-04-28T00:01:00+00:00")
    res = incident_state_manager.transition_incident_state(ack, "resolved", now="2026-04-28T00:02:00+00:00")
    invalid_direct = False
    invalid_back = False
    try:
        incident_state_manager.transition_incident_state(inc, "resolved")
    except ValueError:
        invalid_direct = True
    try:
        incident_state_manager.transition_incident_state(res, "acknowledged")
    except ValueError:
        invalid_back = True
    checks.append(check(
        "incident_state_manager_forward_only_manual_lifecycle",
        ack.state == "acknowledged" and res.state == "resolved" and invalid_direct and invalid_back,
        {"ack": asdict(ack), "resolved": asdict(res), "invalid_direct_blocked": invalid_direct, "invalid_back_blocked": invalid_back},
    ))

    # C: Monitoring Export
    budget_snapshot = {"scopes": [{"scope_id": "system", "allocated_units": 10}], "anomalies": []}
    monitoring = monitoring_export.build_monitoring_export(
        budget_snapshot=budget_snapshot,
        incidents=[inc, ack],
        alerts=alerts,
        aggregated_alerts=aggregated,
    )
    checks.append(check(
        "monitoring_export_contains_read_only_operational_view",
        monitoring["summary"]["incident_count"] == 2
        and monitoring["summary"]["open_incidents"] == 1
        and monitoring["summary"]["alert_count"] == 3
        and monitoring["summary"]["critical_alerts"] == 1
        and "budget_snapshot" in monitoring,
        {"summary": monitoring["summary"], "schema_version": monitoring["schema_version"]},
    ))

    # D: Flood Guard direct evaluation
    conn = fresh_conn("operational_stability_flood")
    now = datetime(2026, 4, 28, 12, 0, tzinfo=timezone.utc)
    cfg = flood_guard.FloodGuardConfig(window_seconds=60, max_tasks_per_window=2, max_cost_units_per_window=5)
    insert_session_decision(conn, actor_id="actor-a", cost=2, created_at=now - timedelta(seconds=10))
    d1 = flood_guard.evaluate_flood_guard(conn, actor_id="actor-a", projected_cost_units=2, config=cfg, now=now)
    insert_session_decision(conn, actor_id="actor-a", cost=2, created_at=now - timedelta(seconds=5))
    d2 = flood_guard.evaluate_flood_guard(conn, actor_id="actor-a", projected_cost_units=1, config=cfg, now=now)
    d3 = flood_guard.evaluate_flood_guard(conn, actor_id="actor-b", projected_cost_units=1, config=cfg, now=now)
    d4 = flood_guard.evaluate_flood_guard(conn, actor_id="actor-a", projected_cost_units=0, config=cfg, now=now)
    checks.append(check(
        "flood_guard_blocks_window_limits_and_fails_closed",
        d1.decision == "continue"
        and d2.decision == "stop" and d2.reason == "FLOOD_TASK_WINDOW_LIMIT"
        and d3.decision == "continue"
        and d4.decision == "stop" and d4.reason == "FLOOD_INVALID_PROJECTED_COST",
        {"below": asdict(d1), "task_limit": asdict(d2), "other_actor": asdict(d3), "invalid": asdict(d4)},
    ))

    # D integration: pipeline must stop at flood_guard before session reservation or runtime work.
    conn2 = fresh_conn("operational_stability_pipeline")
    session_budget_guard.create_session_budget(conn2, session_id="SES-PIPE", max_session_cost_units=100, max_session_tasks=100, max_agent_cost_units=100)
    runtime_guard.create_budget(conn2, task_id="TASK-PIPE", max_steps=10, max_runtime_seconds=100, max_cost_units=100)
    insert_session_decision(conn2, actor_id="actor-pipe", cost=1, created_at=datetime.now(timezone.utc) - timedelta(seconds=1))
    pipeline = guard_orchestrator.evaluate_guard_pipeline(
        conn2,
        enforcement_allowed=True,
        enforcement_reason="capability granted",
        session_id="SES-PIPE",
        task_id="TASK-PIPE",
        actor_id="actor-pipe",
        action_type="external_api_call",
        target="GET:https://api.example.test/v1/search",
        projected_cost_units=1,
        flood_config=flood_guard.FloodGuardConfig(window_seconds=60, max_tasks_per_window=1, max_cost_units_per_window=10),
    )
    session_links = conn2.execute("SELECT COUNT(*) FROM session_task_links WHERE session_id = 'SES-PIPE'").fetchone()[0]
    runtime_steps = conn2.execute("SELECT COUNT(*) FROM runtime_steps WHERE task_id = 'TASK-PIPE'").fetchone()[0]
    checks.append(check(
        "guard_pipeline_blocks_flood_before_session_reservation",
        pipeline.decision == "stop" and pipeline.stage == "flood_guard" and session_links == 0 and runtime_steps == 0,
        {"pipeline": asdict(pipeline), "session_links": session_links, "runtime_steps": runtime_steps},
    ))

    passed = sum(1 for ok, _, _ in checks if ok)
    failed = len(checks) - passed
    print("\nOPERATIONAL STABILITY EVIDENCE REPORT")
    print(f"Summary: {{'total': {len(checks)}, 'passed': {passed}, 'failed': {failed}, 'findings': 0}}")
    return 0 if failed == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
