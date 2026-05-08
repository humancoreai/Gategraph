"""
WHY: v0.8.3 proves scale-relevant fixes: session budget reservation, actual-cost drift handling, schema/version hygiene.
INV: tests exercise additive safety behavior without weakening existing guards.
"""
from __future__ import annotations

import os
import sys
import tempfile
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.database import get_connection, init_db, seed_rules, ensure_runtime_schema, ensure_pattern_schema
from src import runtime_guard, session_budget_guard, event_logger
from src.reason_normalizer import normalize_reason
from audit_evidence import EvidenceRunLog, EvidenceScenarioResult, collect_session_evidence, collect_task_evidence

PROJECT_ROOT = Path(__file__).resolve().parents[1]
LOG_DIR = PROJECT_ROOT / "tests" / "logs"


def fresh_conn():
    tmp = tempfile.NamedTemporaryFile(prefix="gategraph_scale_safety_", suffix=".db", delete=False)
    tmp.close()
    db_path = Path(tmp.name)
    init_db(db_path)
    conn = get_connection(db_path)
    ensure_runtime_schema(conn)
    ensure_pattern_schema(conn)
    session_budget_guard.ensure_session_budget_schema(conn)
    with conn:
        seed_rules(conn)
    return conn, db_path


def close_conn(conn, db_path: Path) -> None:
    conn.close()
    try:
        db_path.unlink()
    except FileNotFoundError:
        pass


def run_actual_step(conn, *, task_id: str, actor_id: str, actual_cost_units: int) -> None:
    runtime_guard.create_budget(conn, task_id=task_id, max_steps=5, max_cost_units=100, repeated_action_limit=10)
    rd = runtime_guard.evaluate_before_step(
        conn,
        task_id=task_id,
        actor_id=actor_id,
        action_type="model_call",
        target=task_id,
        cost_units=actual_cost_units,
    )
    assert rd.decision == "continue", rd


def scenario_reserved_cost_prevents_two_tasks_oversubscribe() -> EvidenceScenarioResult:
    conn, db_path = fresh_conn()
    session_id = "SCALE-RESERVATION"
    try:
        session_budget_guard.create_session_budget(conn, session_id=session_id, max_session_cost_units=10, max_session_tasks=10, max_agent_cost_units=100)

        d1 = session_budget_guard.evaluate_before_task(
            conn, session_id=session_id, task_id="SCALE-RESERVE-A", actor_id="agent-a", projected_cost_units=6
        )
        d2 = session_budget_guard.evaluate_before_task(
            conn, session_id=session_id, task_id="SCALE-RESERVE-B", actor_id="agent-b", projected_cost_units=6
        )

        evidence = collect_session_evidence(conn, session_id)
        links = evidence["session_task_links"]
        passed = d1.decision == "continue" and d2.decision == "stop" and "max_session_cost_units" in d2.reason and len(links) == 1 and links[0]["reserved_cost_units"] == 6
        return EvidenceScenarioResult(
            test_name="reserved_cost_prevents_two_tasks_oversubscribe",
            description="Projected session cost is reserved at allow-time so a second task cannot pass against stale free budget.",
            expected={"first": "continue", "second": "stop", "linked_tasks": 1, "reserved_cost_units": 6},
            actual={"first": d1.decision, "second": d2.decision, "second_reason": d2.reason, "linked_tasks": len(links), "links": links},
            passed=passed,
            severity="info" if passed else "critical",
            notes=[] if passed else ["Session reservation did not prevent oversubscription."],
            evidence=evidence,
        )
    finally:
        close_conn(conn, db_path)


def scenario_actual_cost_drift_blocks_next_task() -> EvidenceScenarioResult:
    conn, db_path = fresh_conn()
    session_id = "SCALE-ACTUAL-DRIFT"
    try:
        session_budget_guard.create_session_budget(conn, session_id=session_id, max_session_cost_units=12, max_session_tasks=10, max_agent_cost_units=100)

        d1 = session_budget_guard.evaluate_before_task(
            conn, session_id=session_id, task_id="SCALE-ACTUAL-A", actor_id="agent-a", projected_cost_units=5
        )
        if d1.decision == "continue":
            run_actual_step(conn, task_id="SCALE-ACTUAL-A", actor_id="agent-a", actual_cost_units=20)

        d2 = session_budget_guard.evaluate_before_task(
            conn, session_id=session_id, task_id="SCALE-ACTUAL-B", actor_id="agent-a", projected_cost_units=1
        )

        session_ev = collect_session_evidence(conn, session_id)
        task_ev = collect_task_evidence(conn, "SCALE-ACTUAL-A")
        passed = d1.decision == "continue" and d2.decision == "stop" and "max_session_cost_units" in d2.reason
        return EvidenceScenarioResult(
            test_name="actual_cost_drift_blocks_next_task",
            description="If actual runtime cost exceeds projected reservation, next session-budget check sees actual overrun.",
            expected={"first": "continue", "second": "stop", "second_reason_contains": "max_session_cost_units"},
            actual={"first": d1.decision, "second": d2.decision, "second_reason": d2.reason},
            passed=passed,
            severity="info" if passed else "critical",
            notes=[] if passed else ["Actual cost overrun was not reflected in subsequent session budget check."],
            evidence={"session": session_ev, "actual_task": task_ev},
        )
    finally:
        close_conn(conn, db_path)


def scenario_reason_normalizer_uses_canonical_prefix() -> EvidenceScenarioResult:
    cases = [
        ("session_budget", "max_session_cost_units exceeded: 12 > 10", "SES_COST_LIMIT"),
        ("session_budget", "max_session_tasks exceeded: 10 >= 10", "SES_TASK_LIMIT"),
        ("runtime_guard", "repeated_action_limit exceeded for signature 'agent-a:delegate:agent-b'", "RT_REPEATED_ACTION"),
    ]
    actual = []
    for stage, reason, expected in cases:
        nr = normalize_reason(stage, reason)
        actual.append({"stage": stage, "reason": reason, "code": nr.code, "expected": expected, "raw_preserved": nr.raw_reason == reason})
    passed = all(item["code"] == item["expected"] and item["raw_preserved"] for item in actual)
    return EvidenceScenarioResult(
        test_name="reason_normalizer_uses_canonical_prefix",
        description="Reason normalization uses explicit canonical prefixes, not broad substring ordering.",
        expected={"all_codes_match": True, "raw_preserved": True},
        actual={"cases": actual},
        passed=passed,
        severity="info" if passed else "medium",
        notes=[] if passed else ["Reason normalization produced unstable or wrong mapping."],
        evidence={"cases": actual},
    )


def scenario_event_schema_version_current() -> EvidenceScenarioResult:
    conn, db_path = fresh_conn()
    try:
        with conn:
            conn.execute(
                """
                INSERT OR IGNORE INTO tasks
                  (task_id, task_type, capabilities, input_source, data_sensitivity, secrets_involved, created_at)
                VALUES ('SCALE-SCHEMA-VERSION', 'schema_test', '[]', 'local', 'internal', 0, datetime('now'))
                """
            )
            event = event_logger.log_event(
                conn,
                event_id="EVT-SCALE-SCHEMA",
                idempotency_key="scale:schema-version",
                correlation_id="COR-SCALE-SCHEMA",
                causation_id=None,
                event_type="schema_version_test",
                task_id="SCALE-SCHEMA-VERSION",
                actor_component="scale_safety_test",
                input_data={},
                evaluation={},
                decision={"status": "logged"},
            )
        row = conn.execute("SELECT schema_version FROM events WHERE event_id = ?", (event.event_id,)).fetchone()
        passed = row["schema_version"] == "0.8.3"
        return EvidenceScenarioResult(
            test_name="event_schema_version_current",
            description="New events must carry current schema version, not stale v0.4 default.",
            expected={"schema_version": "0.8.3"},
            actual={"schema_version": row["schema_version"]},
            passed=passed,
            severity="info" if passed else "medium",
            notes=[] if passed else ["Event schema_version is stale."],
            evidence={"event_id": event.event_id, "schema_version": row["schema_version"]},
        )
    finally:
        close_conn(conn, db_path)


def main() -> int:
    run_id = datetime.now(timezone.utc).strftime("scale_safety_evidence_%Y%m%d_%H%M%S")
    log = EvidenceRunLog(run_id=run_id, started_at=datetime.now(timezone.utc).isoformat())
    scenarios = [
        scenario_reserved_cost_prevents_two_tasks_oversubscribe,
        scenario_actual_cost_drift_blocks_next_task,
        scenario_reason_normalizer_uses_canonical_prefix,
        scenario_event_schema_version_current,
    ]

    for scenario in scenarios:
        result = scenario()
        log.add(result)
        mark = "✓" if result.passed else "✗"
        print(f"{mark} {result.test_name}: {result.actual}")

    log.finish()
    out = log.write(LOG_DIR)
    print("\nSCALE SAFETY EVIDENCE REPORT")
    print(f"Log: {out}")
    print(f"Summary: {log.summary}")
    return 0 if log.summary["failed"] == 0 else 1


if __name__ == "__main__":
    os._exit(main())
