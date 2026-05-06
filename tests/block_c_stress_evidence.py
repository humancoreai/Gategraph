"""
WHY: Block C stress evidence checks runaway/cost behavior with realistic API-shaped flows.
INV: This runner does not grant capabilities or alter core policy semantics; it only exercises public APIs.
SEC: Stress cases must stop before transport once Session/Runtime budgets are exhausted.
"""
from __future__ import annotations

import os
import sys
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Mapping

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.database import get_connection, init_db, seed_rules, ensure_runtime_schema, ensure_pattern_schema
from src import capability_token, event_logger, http_policy, runtime_guard, secret_provider, session_budget_guard
from src.external_api_adapter import ControlledAPIResponse, ExternalAPIRequest, call_controlled_external_api
from audit_evidence import EvidenceRunLog, EvidenceScenarioResult, collect_session_evidence, collect_task_evidence

PROJECT_ROOT = Path(__file__).resolve().parents[1]
LOG_DIR = PROJECT_ROOT / "tests" / "logs"


def fresh_conn():
    tmp = tempfile.NamedTemporaryFile(prefix="gategraph_block_c_", suffix=".db", delete=False)
    tmp.close()
    db_path = Path(tmp.name)
    init_db(db_path)
    conn = get_connection(db_path)
    ensure_runtime_schema(conn)
    ensure_pattern_schema(conn)
    session_budget_guard.ensure_session_budget_schema(conn)
    secret_provider.ensure_secret_schema(conn)
    http_policy.ensure_http_policy_schema(conn)
    with conn:
        seed_rules(conn)
    return conn, db_path


def close_conn(conn, db_path: Path) -> None:
    conn.close()
    try:
        db_path.unlink()
    except FileNotFoundError:
        pass


def prepare_session(conn, *, session_id: str, max_session_cost_units: int, max_session_tasks: int = 50, max_agent_cost_units: int = 60) -> None:
    session_budget_guard.create_session_budget(
        conn,
        session_id=session_id,
        max_session_cost_units=max_session_cost_units,
        max_session_tasks=max_session_tasks,
        max_agent_cost_units=max_agent_cost_units,
    )


def prepare_runtime(conn, *, task_id: str, max_steps: int = 10, max_cost_units: int = 100, repeated_action_limit: int = 10) -> None:
    runtime_guard.create_budget(
        conn,
        task_id=task_id,
        max_steps=max_steps,
        max_cost_units=max_cost_units,
        repeated_action_limit=repeated_action_limit,
    )


def issue_api_token(conn, *, task_id: str):
    with conn:
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
            event_id=f"EVT-BLOCK-C-TOKEN-{task_id}",
            idempotency_key=f"block-c-token-fixture:{task_id}",
            correlation_id=f"COR-BLOCK-C-TOKEN-{task_id}",
            causation_id=None,
            event_type="test_token_fixture",
            task_id=task_id,
            actor_component="block_c_stress_fixture",
            input_data={"requested_capability": "api_call"},
            evaluation={"fixture": True},
            decision={"status": "allow", "final_capabilities": {"api_call": True}},
        )
        decision_id = f"DEC-BLOCK-C-TOKEN-{task_id}"
        conn.execute(
            """
            INSERT OR IGNORE INTO decisions
              (decision_id, task_id, event_id, status, final_caps_json, reason, matched_rules_json, created_at)
            VALUES (?, ?, ?, 'allow', '{"api_call": true}', 'block c api token fixture', '[]', datetime('now'))
            """,
            (decision_id, task_id, event.event_id),
        )
        return capability_token.issue_token(conn, decision_id, task_id, {"api_call": True})


def request(*, request_id: str, session_id: str, task_id: str, actor_id: str = "agent-block-c", projected_cost_units: int = 1, endpoint: str = "/mock/block-c") -> ExternalAPIRequest:
    return ExternalAPIRequest(
        request_id=request_id,
        session_id=session_id,
        task_id=task_id,
        actor_id=actor_id,
        endpoint=endpoint,
        method="POST",
        payload_summary="block c stress payload redacted",
        projected_cost_units=projected_cost_units,
        timeout_ms=100,
        mock_behavior="success",
        requested_capability="api_call",
        secret_ref_id=None,
    )


def make_transport(calls: list):
    def fake_transport(req: ExternalAPIRequest, headers: Mapping[str, str]) -> ControlledAPIResponse:
        calls.append({"request_id": req.request_id, "task_id": req.task_id, "headers": dict(headers)})
        return ControlledAPIResponse(200, "block c transport success")
    return fake_transport


def scenario_micro_flood_stops_at_session_budget() -> EvidenceScenarioResult:
    conn, db_path = fresh_conn(); session_id = "BLOCK-C-MICRO-FLOOD"; calls = []
    try:
        prepare_session(conn, session_id=session_id, max_session_cost_units=3, max_session_tasks=10, max_agent_cost_units=10)
        results = []
        for idx in range(1, 6):
            task_id = f"BLOCK-C-MICRO-{idx}"
            prepare_runtime(conn, task_id=task_id, max_steps=5, max_cost_units=10, repeated_action_limit=5)
            tok = issue_api_token(conn, task_id=task_id)
            results.append(call_controlled_external_api(conn, request=request(request_id=f"REQ-BLOCK-C-MICRO-{idx}", session_id=session_id, task_id=task_id, projected_cost_units=1), token=tok, transport=make_transport(calls)))
        session_ev = collect_session_evidence(conn, session_id)
        decisions = [r.decision for r in results]
        stages = [r.stage for r in results]
        passed = decisions[:3] == ["completed", "completed", "completed"] and decisions[3:] == ["blocked", "blocked"] and stages[3:] == ["session_budget", "session_budget"] and len(calls) == 3 and len(session_ev["session_task_links"]) == 3
        return EvidenceScenarioResult(
            "micro_flood_stops_at_session_budget",
            "Many individually cheap API-shaped actions must stop once global session budget is reserved.",
            {"completed": 3, "blocked_stage": "session_budget", "transport_calls": 3, "reserved_links": 3},
            {"decisions": decisions, "stages": stages, "transport_calls": len(calls), "reserved_links": len(session_ev["session_task_links"])},
            passed,
            "info" if passed else "critical",
            [] if passed else ["Micro-flood exceeded reserved session budget or wrong stop stage."],
            {"session": session_ev},
        )
    finally:
        close_conn(conn, db_path)


def scenario_parallel_agent_budget_stops_second_task() -> EvidenceScenarioResult:
    conn, db_path = fresh_conn(); session_id = "BLOCK-C-AGENT-BUDGET"; actor_id = "agent-same"; calls = []
    try:
        prepare_session(conn, session_id=session_id, max_session_cost_units=20, max_session_tasks=10, max_agent_cost_units=3)
        results = []
        for idx in range(1, 3):
            task_id = f"BLOCK-C-AGENT-{idx}"
            prepare_runtime(conn, task_id=task_id, max_steps=5, max_cost_units=10, repeated_action_limit=5)
            tok = issue_api_token(conn, task_id=task_id)
            results.append(call_controlled_external_api(conn, request=request(request_id=f"REQ-BLOCK-C-AGENT-{idx}", session_id=session_id, task_id=task_id, actor_id=actor_id, projected_cost_units=2), token=tok, transport=make_transport(calls)))
        session_ev = collect_session_evidence(conn, session_id)
        passed = results[0].decision == "completed" and results[1].decision == "blocked" and results[1].stage == "session_budget" and "max_agent_cost_units" in results[1].reason and len(calls) == 1 and len(session_ev["session_task_links"]) == 1
        return EvidenceScenarioResult(
            "parallel_agent_budget_stops_second_task",
            "Same-agent parallel task fan-out must respect agent-level budget, not just global session budget.",
            {"first": "completed", "second": "blocked", "reason_contains": "max_agent_cost_units", "transport_calls": 1},
            {"decisions": [r.decision for r in results], "stages": [r.stage for r in results], "second_reason": results[1].reason, "transport_calls": len(calls), "reserved_links": len(session_ev["session_task_links"])},
            passed,
            "info" if passed else "critical",
            [] if passed else ["Agent-level budget did not stop fan-out before transport."],
            {"session": session_ev},
        )
    finally:
        close_conn(conn, db_path)


def scenario_budget_edge_exact_then_stop() -> EvidenceScenarioResult:
    conn, db_path = fresh_conn(); session_id = "BLOCK-C-EDGE-BUDGET"; calls = []
    try:
        prepare_session(conn, session_id=session_id, max_session_cost_units=5, max_session_tasks=10, max_agent_cost_units=10)
        costs = [4, 1, 1]
        results = []
        for idx, cost in enumerate(costs, start=1):
            task_id = f"BLOCK-C-EDGE-{idx}"
            prepare_runtime(conn, task_id=task_id, max_steps=5, max_cost_units=10, repeated_action_limit=5)
            tok = issue_api_token(conn, task_id=task_id)
            results.append(call_controlled_external_api(conn, request=request(request_id=f"REQ-BLOCK-C-EDGE-{idx}", session_id=session_id, task_id=task_id, projected_cost_units=cost), token=tok, transport=make_transport(calls)))
        session_ev = collect_session_evidence(conn, session_id)
        passed = [r.decision for r in results] == ["completed", "completed", "blocked"] and results[2].stage == "session_budget" and len(calls) == 2 and len(session_ev["session_task_links"]) == 2
        return EvidenceScenarioResult(
            "budget_edge_exact_then_stop",
            "A final action exactly filling remaining budget is allowed; the next action stops fail-closed.",
            {"decisions": ["completed", "completed", "blocked"], "transport_calls": 2, "reserved_links": 2},
            {"decisions": [r.decision for r in results], "stages": [r.stage for r in results], "transport_calls": len(calls), "reserved_links": len(session_ev["session_task_links"])},
            passed,
            "info" if passed else "critical",
            [] if passed else ["Budget boundary was off by one or did not stop after exact exhaustion."],
            {"session": session_ev},
        )
    finally:
        close_conn(conn, db_path)


def scenario_same_task_loop_stops_at_runtime_before_policy() -> EvidenceScenarioResult:
    conn, db_path = fresh_conn(); session_id = "BLOCK-C-RUNTIME-LOOP"; task_id = "BLOCK-C-RUNTIME-LOOP-TASK"; calls = []
    try:
        prepare_session(conn, session_id=session_id, max_session_cost_units=20, max_session_tasks=10, max_agent_cost_units=20)
        prepare_runtime(conn, task_id=task_id, max_steps=10, max_cost_units=20, repeated_action_limit=2)
        tok = issue_api_token(conn, task_id=task_id)
        results = []
        for idx in range(1, 4):
            results.append(call_controlled_external_api(conn, request=request(request_id=f"REQ-BLOCK-C-LOOP-{idx}", session_id=session_id, task_id=task_id, projected_cost_units=1, endpoint="/mock/repeated-target"), token=tok, transport=make_transport(calls)))
        task_ev = collect_task_evidence(conn, task_id)
        session_ev = collect_session_evidence(conn, session_id)
        passed = [r.decision for r in results] == ["completed", "completed", "blocked"] and results[2].stage == "runtime_guard" and "repeated_action_limit" in results[2].reason and len(calls) == 2 and len(task_ev["runtime_steps"]) == 2 and len(session_ev["session_task_links"]) == 1
        return EvidenceScenarioResult(
            "same_task_loop_stops_at_runtime_before_policy",
            "Repeated same-task API-shaped loop must stop at Runtime Guard before HTTP policy/transport executes again.",
            {"decisions": ["completed", "completed", "blocked"], "blocked_stage": "runtime_guard", "transport_calls": 2, "runtime_steps": 2},
            {"decisions": [r.decision for r in results], "stages": [r.stage for r in results], "third_reason": results[2].reason, "transport_calls": len(calls), "runtime_steps": len(task_ev["runtime_steps"]), "reserved_links": len(session_ev["session_task_links"])},
            passed,
            "info" if passed else "critical",
            [] if passed else ["Runtime repeated-action loop did not stop before the third transport."],
            {"task": task_ev, "session": session_ev},
        )
    finally:
        close_conn(conn, db_path)


def main() -> int:
    run_id = datetime.now(timezone.utc).strftime("block_c_stress_evidence_%Y%m%d_%H%M%S")
    log = EvidenceRunLog(run_id=run_id, started_at=datetime.now(timezone.utc).isoformat())
    scenarios = [
        scenario_micro_flood_stops_at_session_budget,
        scenario_parallel_agent_budget_stops_second_task,
        scenario_budget_edge_exact_then_stop,
        scenario_same_task_loop_stops_at_runtime_before_policy,
    ]
    for scenario in scenarios:
        result = scenario()
        log.add(result)
        mark = "✓" if result.passed else "✗"
        print(f"{mark} {result.test_name}: {result.actual}")
    log.finish()
    out = log.write(LOG_DIR)
    print("\nBLOCK C STRESS EVIDENCE REPORT")
    print(f"Log: {out}")
    print(f"Summary: {log.summary}")
    return 0 if log.summary["failed"] == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
