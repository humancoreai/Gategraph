"""
WHY: Evidence tests for runaway/cost-control edge cases that can create silent under-accounting.
INV: tests only exercise guard behavior; no production rules are mutated.
SEC: zero/negative costs must fail closed because they can otherwise create free or budget-increasing work.
"""
from __future__ import annotations

import os
import sys
import tempfile
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.database import get_connection, init_db, seed_rules, ensure_runtime_schema, ensure_pattern_schema
from src import runtime_guard, session_budget_guard, event_logger, capability_token
from src.external_api_adapter import ExternalAPIRequest, call_mock_external_api
from audit_evidence import EvidenceRunLog, EvidenceScenarioResult, collect_task_evidence, collect_session_evidence

PROJECT_ROOT = Path(__file__).resolve().parents[1]
LOG_DIR = PROJECT_ROOT / "tests" / "logs"


def fresh_conn():
    tmp = tempfile.NamedTemporaryFile(prefix="gategraph_runaway_cost_", suffix=".db", delete=False)
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


def issue_api_token(conn, *, task_id: str):
    conn.execute(
        """
        INSERT OR IGNORE INTO tasks
          (task_id, task_type, capabilities, input_source, data_sensitivity, secrets_involved, created_at)
        VALUES (?, 'external_api_call', '["api_call"]', 'local', 'internal', 0, datetime('now'))
        """,
        (task_id,),
    )
    event = event_logger.log_event(
        conn,
        event_id=f"EVT-RUNAWAY-TOKEN-{task_id}",
        idempotency_key=f"runaway-cost-token:{task_id}",
        correlation_id=f"COR-RUNAWAY-TOKEN-{task_id}",
        causation_id=None,
        event_type="test_fixture_decision",
        task_id=task_id,
        actor_component="runaway_cost_evidence",
        input_data={},
        evaluation={},
        decision={"status": "allow", "final_capabilities": {"api_call": True}},
    )
    decision_id = f"DEC-RUNAWAY-{task_id}"
    conn.execute(
        """
        INSERT OR IGNORE INTO decisions
          (decision_id, task_id, event_id, status, final_caps_json, reason, matched_rules_json, created_at)
        VALUES (?, ?, ?, 'allow', '{"api_call": true}', 'test fixture api token', '[]', datetime('now'))
        """,
        (decision_id, task_id, event.event_id),
    )
    return capability_token.issue_token(conn, decision_id, task_id, {"api_call": True})


def make_request(*, request_id: str, session_id: str, task_id: str, projected_cost_units: int) -> ExternalAPIRequest:
    return ExternalAPIRequest(
        request_id=request_id,
        session_id=session_id,
        task_id=task_id,
        actor_id="agent-cost-edge",
        endpoint="/mock/cost-edge",
        method="POST",
        payload_summary="redacted cost edge test",
        projected_cost_units=projected_cost_units,
        timeout_ms=100,
        mock_behavior="success",
    )


def scenario_session_negative_projected_cost_fails_closed() -> EvidenceScenarioResult:
    conn, db_path = fresh_conn(); session_id = "RUNAWAY-NEG-PROJECTED"; task_id = "RUNAWAY-NEG-PROJECTED-TASK"
    try:
        session_budget_guard.create_session_budget(conn, session_id=session_id, max_session_cost_units=10, max_session_tasks=10, max_agent_cost_units=10)
        decision = session_budget_guard.evaluate_before_task(
            conn, session_id=session_id, task_id=task_id, actor_id="agent-a", projected_cost_units=-5
        )
        evidence = collect_session_evidence(conn, session_id)
        passed = decision.decision == "stop" and "invalid projected_cost_units" in decision.reason and len(evidence["session_task_links"]) == 0
        return EvidenceScenarioResult(
            "session_negative_projected_cost_fails_closed",
            "Negative projected costs must not reserve negative budget or create a session task link.",
            {"decision": "stop", "reason_contains": "invalid projected_cost_units", "linked_tasks": 0},
            {"decision": decision.decision, "reason": decision.reason, "linked_tasks": len(evidence["session_task_links"])},
            passed,
            "info" if passed else "critical",
            [] if passed else ["Negative projected cost was not blocked before reservation."],
            evidence,
        )
    finally:
        close_conn(conn, db_path)


def scenario_runtime_zero_cost_fails_closed_without_step() -> EvidenceScenarioResult:
    conn, db_path = fresh_conn(); task_id = "RUNAWAY-ZERO-RUNTIME"
    try:
        runtime_guard.create_budget(conn, task_id=task_id, max_steps=5, max_cost_units=10, repeated_action_limit=10)
        decision = runtime_guard.evaluate_before_step(
            conn, task_id=task_id, actor_id="agent-a", action_type="model_call", target="free-work", cost_units=0
        )
        evidence = collect_task_evidence(conn, task_id)
        passed = decision.decision == "stop" and "invalid cost_units" in decision.reason and len(evidence["runtime_steps"]) == 0
        return EvidenceScenarioResult(
            "runtime_zero_cost_fails_closed_without_step",
            "Zero-cost runtime work must not be accepted because it can hide unbounded work.",
            {"decision": "stop", "reason_contains": "invalid cost_units", "runtime_steps": 0},
            {"decision": decision.decision, "reason": decision.reason, "runtime_steps": len(evidence["runtime_steps"])},
            passed,
            "info" if passed else "critical",
            [] if passed else ["Zero-cost runtime step was accepted."],
            evidence,
        )
    finally:
        close_conn(conn, db_path)


def scenario_external_api_negative_cost_blocked_before_runtime() -> EvidenceScenarioResult:
    conn, db_path = fresh_conn(); session_id = "RUNAWAY-API-NEG"; task_id = "RUNAWAY-API-NEG-TASK"
    try:
        session_budget_guard.create_session_budget(conn, session_id=session_id, max_session_cost_units=10, max_session_tasks=10, max_agent_cost_units=10)
        runtime_guard.create_budget(conn, task_id=task_id, max_steps=5, max_cost_units=10, repeated_action_limit=10)
        result = call_mock_external_api(
            conn,
            request=make_request(request_id="REQ-RUNAWAY-API-NEG", session_id=session_id, task_id=task_id, projected_cost_units=-1),
            token=issue_api_token(conn, task_id=task_id),
        )
        task_ev = collect_task_evidence(conn, task_id)
        session_ev = collect_session_evidence(conn, session_id)
        passed = (
            result.decision == "blocked"
            and result.stage == "session_budget"
            and result.normalized_reason["code"] == "SES_INVALID_COST"
            and len(task_ev["runtime_steps"]) == 0
            and len(session_ev["session_task_links"]) == 0
        )
        return EvidenceScenarioResult(
            "external_api_negative_cost_blocked_before_runtime",
            "External API request with negative projected cost must stop at Session Budget and never spend Runtime work.",
            {"decision": "blocked", "stage": "session_budget", "code": "SES_INVALID_COST", "runtime_steps": 0, "linked_tasks": 0},
            {"decision": result.decision, "stage": result.stage, "code": result.normalized_reason["code"], "runtime_steps": len(task_ev["runtime_steps"]), "linked_tasks": len(session_ev["session_task_links"])},
            passed,
            "info" if passed else "critical",
            [] if passed else ["Negative-cost API call reached runtime/action path."],
            {"task": task_ev, "session": session_ev},
        )
    finally:
        close_conn(conn, db_path)


def main() -> int:
    run_id = datetime.now(timezone.utc).strftime("runaway_cost_evidence_%Y%m%d_%H%M%S")
    log = EvidenceRunLog(run_id=run_id, started_at=datetime.now(timezone.utc).isoformat())
    scenarios = [
        scenario_session_negative_projected_cost_fails_closed,
        scenario_runtime_zero_cost_fails_closed_without_step,
        scenario_external_api_negative_cost_blocked_before_runtime,
    ]
    for scenario in scenarios:
        result = scenario()
        log.add(result)
        mark = "✓" if result.passed else "✗"
        print(f"{mark} {result.test_name}: {result.actual}")
    log.finish()
    out = log.write(LOG_DIR)
    print("\nRUNAWAY COST EVIDENCE REPORT")
    print(f"Log: {out}")
    print(f"Summary: {log.summary}")
    return 0 if log.summary["failed"] == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
