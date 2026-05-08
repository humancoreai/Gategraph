"""
WHY: External API evidence tests prove all outbound calls pass Guard Orchestration before execution.
INV: v0.8.4 uses deterministic mock APIs only; no network calls are made.
"""
from __future__ import annotations

import os
import sys
import tempfile
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.database import get_connection, init_db, seed_rules, ensure_runtime_schema, ensure_pattern_schema
from src import runtime_guard, session_budget_guard
from src.external_api_adapter import ExternalAPIRequest, call_mock_external_api
from audit_evidence import EvidenceRunLog, EvidenceScenarioResult, collect_task_evidence, collect_session_evidence

PROJECT_ROOT = Path(__file__).resolve().parents[1]
LOG_DIR = PROJECT_ROOT / "tests" / "logs"


def fresh_conn():
    tmp = tempfile.NamedTemporaryFile(prefix="gategraph_external_api_", suffix=".db", delete=False)
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


def prepare_allowed(conn, *, session_id: str, task_id: str, session_cost: int = 100, runtime_cost: int = 100) -> None:
    session_budget_guard.create_session_budget(conn, session_id=session_id, max_session_cost_units=session_cost, max_session_tasks=20, max_agent_cost_units=session_cost)
    runtime_guard.create_budget(conn, task_id=task_id, max_steps=10, max_cost_units=runtime_cost, repeated_action_limit=10)


def make_request(*, request_id: str, session_id: str, task_id: str, actor_id: str = "agent-api", projected_cost_units: int = 1, behavior: str = "success") -> ExternalAPIRequest:
    return ExternalAPIRequest(
        request_id=request_id,
        session_id=session_id,
        task_id=task_id,
        actor_id=actor_id,
        endpoint="/mock/search",
        method="POST",
        payload_summary="redacted test payload",
        projected_cost_units=projected_cost_units,
        timeout_ms=100,
        mock_behavior=behavior,
    )


def scenario_allowed_mock_call_completed() -> EvidenceScenarioResult:
    conn, db_path = fresh_conn()
    session_id = "API-SUCCESS"
    task_id = "API-SUCCESS-TASK"
    try:
        prepare_allowed(conn, session_id=session_id, task_id=task_id)
        result = call_mock_external_api(
            conn,
            request=make_request(request_id="REQ-API-SUCCESS", session_id=session_id, task_id=task_id),
            enforcement_allowed=True,
            enforcement_reason="allowed",
        )
        evidence = collect_task_evidence(conn, task_id)
        api_events = [e for e in evidence["events"] if e["type"] == "external_api_call"]
        passed = result.decision == "completed" and result.stage == "action_ready" and result.status_code == 200 and len(api_events) == 1
        return EvidenceScenarioResult(
            test_name="allowed_mock_call_completed",
            description="Allowed mock API call must pass guards and produce one audit event.",
            expected={"decision": "completed", "stage": "action_ready", "status_code": 200, "api_events": 1},
            actual={"decision": result.decision, "stage": result.stage, "status_code": result.status_code, "api_events": len(api_events)},
            passed=passed,
            severity="info" if passed else "high",
            notes=[] if passed else ["Allowed mock API call did not complete/audit cleanly."],
            evidence=evidence,
        )
    finally:
        close_conn(conn, db_path)


def scenario_no_token_blocks_before_api() -> EvidenceScenarioResult:
    conn, db_path = fresh_conn()
    session_id = "API-NO-TOKEN"
    task_id = "API-NO-TOKEN-TASK"
    try:
        prepare_allowed(conn, session_id=session_id, task_id=task_id)
        result = call_mock_external_api(
            conn,
            request=make_request(request_id="REQ-API-NO-TOKEN", session_id=session_id, task_id=task_id),
            enforcement_allowed=False,
            enforcement_reason="no capability token provided",
        )
        task_ev = collect_task_evidence(conn, task_id)
        session_ev = collect_session_evidence(conn, session_id)
        passed = result.decision == "blocked" and result.stage == "enforcement" and result.normalized_reason["code"] == "ENF_NO_TOKEN" and len(session_ev["session_budget_decisions"]) == 0 and len(task_ev["runtime_decisions"]) == 0
        return EvidenceScenarioResult(
            test_name="no_token_blocks_before_api",
            description="API call without token must stop at Enforcement before budget/runtime work.",
            expected={"decision": "blocked", "stage": "enforcement", "session_decisions": 0, "runtime_decisions": 0},
            actual={"decision": result.decision, "stage": result.stage, "code": result.normalized_reason["code"], "session_decisions": len(session_ev["session_budget_decisions"]), "runtime_decisions": len(task_ev["runtime_decisions"])},
            passed=passed,
            severity="info" if passed else "critical",
            notes=[] if passed else ["No-token API call was not blocked at Enforcement."],
            evidence={"task": task_ev, "session": session_ev},
        )
    finally:
        close_conn(conn, db_path)


def scenario_session_budget_blocks_expensive_api() -> EvidenceScenarioResult:
    conn, db_path = fresh_conn()
    session_id = "API-SESSION-STOP"
    task_id = "API-SESSION-STOP-TASK"
    try:
        prepare_allowed(conn, session_id=session_id, task_id=task_id, session_cost=5, runtime_cost=100)
        result = call_mock_external_api(
            conn,
            request=make_request(request_id="REQ-API-SESSION-STOP", session_id=session_id, task_id=task_id, projected_cost_units=6),
            enforcement_allowed=True,
            enforcement_reason="allowed",
        )
        task_ev = collect_task_evidence(conn, task_id)
        passed = result.decision == "blocked" and result.stage == "session_budget" and result.normalized_reason["code"] == "SES_COST_LIMIT" and len(task_ev["runtime_decisions"]) == 0
        return EvidenceScenarioResult(
            test_name="session_budget_blocks_expensive_api",
            description="Expensive API call must stop at Session Budget before Runtime Guard.",
            expected={"decision": "blocked", "stage": "session_budget", "code": "SES_COST_LIMIT", "runtime_decisions": 0},
            actual={"decision": result.decision, "stage": result.stage, "code": result.normalized_reason["code"], "runtime_decisions": len(task_ev["runtime_decisions"])},
            passed=passed,
            severity="info" if passed else "high",
            notes=[] if passed else ["Session budget did not block expensive API call."],
            evidence=task_ev,
        )
    finally:
        close_conn(conn, db_path)


def scenario_runtime_budget_blocks_repeated_api() -> EvidenceScenarioResult:
    conn, db_path = fresh_conn()
    session_id = "API-RUNTIME-REPEAT"
    task_id = "API-RUNTIME-REPEAT-TASK"
    try:
        session_budget_guard.create_session_budget(conn, session_id=session_id, max_session_cost_units=100, max_session_tasks=20, max_agent_cost_units=100)
        runtime_guard.create_budget(conn, task_id=task_id, max_steps=10, max_cost_units=100, repeated_action_limit=1)

        r1 = call_mock_external_api(conn, request=make_request(request_id="REQ-API-REPEAT-1", session_id=session_id, task_id=task_id), enforcement_allowed=True, enforcement_reason="allowed")
        r2 = call_mock_external_api(conn, request=make_request(request_id="REQ-API-REPEAT-2", session_id=session_id, task_id=task_id), enforcement_allowed=True, enforcement_reason="allowed")

        task_ev = collect_task_evidence(conn, task_id)
        passed = r1.decision == "completed" and r2.decision == "blocked" and r2.stage == "runtime_guard" and r2.normalized_reason["code"] == "RT_REPEATED_ACTION"
        return EvidenceScenarioResult(
            test_name="runtime_budget_blocks_repeated_api",
            description="Repeated same API call must stop at Runtime Guard.",
            expected={"first": "completed", "second": "blocked", "second_code": "RT_REPEATED_ACTION"},
            actual={"first": r1.decision, "second": r2.decision, "second_stage": r2.stage, "second_code": r2.normalized_reason["code"]},
            passed=passed,
            severity="info" if passed else "high",
            notes=[] if passed else ["Runtime repeated-action protection did not block repeated API call."],
            evidence=task_ev,
        )
    finally:
        close_conn(conn, db_path)


def scenario_api_timeout_audited_as_failure() -> EvidenceScenarioResult:
    conn, db_path = fresh_conn()
    session_id = "API-TIMEOUT"
    task_id = "API-TIMEOUT-TASK"
    try:
        prepare_allowed(conn, session_id=session_id, task_id=task_id)
        result = call_mock_external_api(
            conn,
            request=make_request(request_id="REQ-API-TIMEOUT", session_id=session_id, task_id=task_id, behavior="timeout"),
            enforcement_allowed=True,
            enforcement_reason="allowed",
        )
        evidence = collect_task_evidence(conn, task_id)
        api_events = [e for e in evidence["events"] if e["type"] == "external_api_call"]
        passed = result.decision == "failed" and "timeout" in result.response_summary and len(api_events) == 1
        return EvidenceScenarioResult(
            test_name="api_timeout_audited_as_failure",
            description="Mock API timeout must be audited as execution failure, not authorization failure.",
            expected={"decision": "failed", "api_events": 1, "response_contains": "timeout"},
            actual={"decision": result.decision, "response_summary": result.response_summary, "api_events": len(api_events)},
            passed=passed,
            severity="info" if passed else "medium",
            notes=[] if passed else ["Timeout was not audited correctly."],
            evidence=evidence,
        )
    finally:
        close_conn(conn, db_path)


def scenario_api_rate_limit_audited_as_failure() -> EvidenceScenarioResult:
    conn, db_path = fresh_conn()
    session_id = "API-RATE"
    task_id = "API-RATE-TASK"
    try:
        prepare_allowed(conn, session_id=session_id, task_id=task_id)
        result = call_mock_external_api(
            conn,
            request=make_request(request_id="REQ-API-RATE", session_id=session_id, task_id=task_id, behavior="rate_limit"),
            enforcement_allowed=True,
            enforcement_reason="allowed",
        )
        passed = result.decision == "failed" and result.status_code == 429 and "rate limit" in result.response_summary
        return EvidenceScenarioResult(
            test_name="api_rate_limit_audited_as_failure",
            description="Mock API rate-limit must be audited as failure with 429 status.",
            expected={"decision": "failed", "status_code": 429},
            actual={"decision": result.decision, "status_code": result.status_code, "response_summary": result.response_summary},
            passed=passed,
            severity="info" if passed else "medium",
            notes=[] if passed else ["Rate limit was not represented correctly."],
            evidence=collect_task_evidence(conn, task_id),
        )
    finally:
        close_conn(conn, db_path)


def scenario_untrusted_api_response_is_data() -> EvidenceScenarioResult:
    conn, db_path = fresh_conn()
    session_id = "API-UNTRUSTED"
    task_id = "API-UNTRUSTED-TASK"
    try:
        prepare_allowed(conn, session_id=session_id, task_id=task_id)
        result = call_mock_external_api(
            conn,
            request=make_request(request_id="REQ-API-UNTRUSTED", session_id=session_id, task_id=task_id, behavior="untrusted_response"),
            enforcement_allowed=True,
            enforcement_reason="allowed",
        )
        evidence = collect_task_evidence(conn, task_id)
        api_events = [e for e in evidence["events"] if e["type"] == "external_api_call"]
        decision_json = api_events[0]["decision"] if api_events else {}
        passed = result.decision == "completed" and "data, not instructions" in result.response_summary and decision_json.get("status") == "completed"
        return EvidenceScenarioResult(
            test_name="untrusted_api_response_is_data",
            description="Untrusted API response must be captured as data only, not interpreted as instruction.",
            expected={"decision": "completed", "response_contains": "data, not instructions"},
            actual={"decision": result.decision, "response_summary": result.response_summary},
            passed=passed,
            severity="info" if passed else "high",
            notes=[] if passed else ["Untrusted API response was not represented as data-only."],
            evidence=evidence,
        )
    finally:
        close_conn(conn, db_path)


def main() -> int:
    run_id = datetime.now(timezone.utc).strftime("external_api_evidence_%Y%m%d_%H%M%S")
    log = EvidenceRunLog(run_id=run_id, started_at=datetime.now(timezone.utc).isoformat())
    scenarios = [
        scenario_allowed_mock_call_completed,
        scenario_no_token_blocks_before_api,
        scenario_session_budget_blocks_expensive_api,
        scenario_runtime_budget_blocks_repeated_api,
        scenario_api_timeout_audited_as_failure,
        scenario_api_rate_limit_audited_as_failure,
        scenario_untrusted_api_response_is_data,
    ]

    for scenario in scenarios:
        result = scenario()
        log.add(result)
        mark = "✓" if result.passed else "✗"
        print(f"{mark} {result.test_name}: {result.actual}")

    log.finish()
    out = log.write(LOG_DIR)
    print("\nEXTERNAL API EVIDENCE REPORT")
    print(f"Log: {out}")
    print(f"Summary: {log.summary}")
    return 0 if log.summary["failed"] == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
