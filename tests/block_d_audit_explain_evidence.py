"""
WHY: Block D proves that Audit + Explain can reconstruct complete allow/block/fail flows from persisted evidence.
INV: These tests do not change production decisions; they verify reviewer-facing trace completeness.
SEC: secret values must never appear in trace or audit output.
"""
from __future__ import annotations

import os
import sys
import tempfile
from pathlib import Path
from typing import Mapping

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.database import get_connection, init_db, seed_rules, ensure_runtime_schema, ensure_pattern_schema
from src import runtime_guard, session_budget_guard, event_logger, capability_token
from src.external_api_adapter import ControlledAPIResponse, ExternalAPIRequest, call_controlled_external_api, call_mock_external_api
from src.explain_trace import build_task_trace, contains_secret_value
from src.http_policy import register_api_endpoint_policy
from src.secret_provider import register_env_secret_ref
from audit_evidence import EvidenceRunLog, EvidenceScenarioResult

PROJECT_ROOT = Path(__file__).resolve().parents[1]
LOG_DIR = PROJECT_ROOT / "tests" / "logs"


def fresh_conn():
    tmp = tempfile.NamedTemporaryFile(prefix="gategraph_block_d_", suffix=".db", delete=False)
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


def prepare_allowed(conn, *, session_id: str, task_id: str, session_cost: int = 100, runtime_cost: int = 100, repeated_action_limit: int = 10) -> None:
    session_budget_guard.create_session_budget(
        conn,
        session_id=session_id,
        max_session_cost_units=session_cost,
        max_session_tasks=20,
        max_agent_cost_units=session_cost,
    )
    runtime_guard.create_budget(
        conn,
        task_id=task_id,
        max_steps=10,
        max_cost_units=runtime_cost,
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
            event_id=f"EVT-BLOCKD-TOKEN-{task_id}",
            idempotency_key=f"block-d-token-fixture:{task_id}",
            correlation_id=f"COR-BLOCKD-TOKEN-{task_id}",
            causation_id=None,
            event_type="test_token_fixture",
            task_id=task_id,
            actor_component="block_d_test_fixture",
            input_data={"requested_capability": "api_call"},
            evaluation={"fixture": True},
            decision={"status": "allow", "final_capabilities": {"api_call": True}},
        )
        decision_id = f"DEC-BLOCKD-TOKEN-{task_id}"
        conn.execute(
            """
            INSERT OR IGNORE INTO decisions
              (decision_id, task_id, event_id, status, final_caps_json, reason, matched_rules_json, created_at)
            VALUES (?, ?, ?, 'allow', '{"api_call": true}', 'block d test fixture api token', '[]', datetime('now'))
            """,
            (decision_id, task_id, event.event_id),
        )
        return capability_token.issue_token(conn, decision_id, task_id, {"api_call": True})


def mock_request(*, request_id: str, session_id: str, task_id: str, projected_cost_units: int = 1) -> ExternalAPIRequest:
    return ExternalAPIRequest(
        request_id=request_id,
        session_id=session_id,
        task_id=task_id,
        actor_id="agent-block-d",
        endpoint="/mock/explain",
        method="POST",
        payload_summary="redacted block d payload",
        projected_cost_units=projected_cost_units,
        timeout_ms=100,
        mock_behavior="success",
    )


def realish_request(*, request_id: str, session_id: str, task_id: str, endpoint: str, secret_ref_id: str | None = None) -> ExternalAPIRequest:
    return ExternalAPIRequest(
        request_id=request_id,
        session_id=session_id,
        task_id=task_id,
        actor_id="agent-block-d",
        endpoint=endpoint,
        method="POST",
        payload_summary="redacted block d http payload",
        projected_cost_units=1,
        timeout_ms=100,
        mock_behavior="success",
        secret_ref_id=secret_ref_id,
    )


def transport_success(request: ExternalAPIRequest, headers: Mapping[str, str]) -> ControlledAPIResponse:
    return ControlledAPIResponse(200, f"transport headers present={bool(headers)}")


def scenario_completed_flow_reconstructs_action_ready() -> EvidenceScenarioResult:
    conn, db_path = fresh_conn(); session_id = "BD-COMPLETE"; task_id = "BD-COMPLETE-TASK"
    try:
        prepare_allowed(conn, session_id=session_id, task_id=task_id)
        result = call_mock_external_api(conn, request=mock_request(request_id="REQ-BD-COMPLETE", session_id=session_id, task_id=task_id), token=issue_api_token(conn, task_id=task_id))
        trace = build_task_trace(conn, task_id)
        passed = (
            result.decision == "completed"
            and trace["final_status"] == "completed"
            and trace["final_stage"] == "action_ready"
            and trace["final_reason_code"] == "OK_ACTION_READY"
            and trace["counts"]["api_events"] == 1
            and trace["counts"]["session_budget_decisions"] >= 1
            and trace["counts"]["runtime_decisions"] >= 1
            and trace["summary"].startswith("Action completed")
        )
        return EvidenceScenarioResult(
            "completed_flow_reconstructs_action_ready",
            "A successful API-shaped action must be reconstructable from audit events, session decisions, runtime decisions, and normalized reason.",
            {"status": "completed", "stage": "action_ready", "code": "OK_ACTION_READY"},
            {"status": trace["final_status"], "stage": trace["final_stage"], "code": trace["final_reason_code"], "counts": trace["counts"]},
            passed,
            "info" if passed else "high",
            [] if passed else ["Completed flow was not reconstructable from persisted evidence."],
            trace,
        )
    finally:
        close_conn(conn, db_path)


def scenario_enforcement_block_reconstructs_no_work() -> EvidenceScenarioResult:
    conn, db_path = fresh_conn(); session_id = "BD-NO-TOKEN"; task_id = "BD-NO-TOKEN-TASK"
    try:
        prepare_allowed(conn, session_id=session_id, task_id=task_id)
        result = call_mock_external_api(conn, request=mock_request(request_id="REQ-BD-NO-TOKEN", session_id=session_id, task_id=task_id), token=None)
        trace = build_task_trace(conn, task_id)
        passed = (
            result.decision == "blocked"
            and trace["final_status"] == "blocked"
            and trace["final_stage"] == "enforcement"
            and trace["final_reason_code"] == "ENF_NO_TOKEN"
            and trace["counts"]["session_budget_decisions"] == 0
            and trace["counts"]["runtime_decisions"] == 0
        )
        return EvidenceScenarioResult(
            "enforcement_block_reconstructs_no_work",
            "A no-token action must be explainable as an Enforcement stop with no downstream budget/runtime work.",
            {"status": "blocked", "stage": "enforcement", "code": "ENF_NO_TOKEN", "downstream_work": 0},
            {"status": trace["final_status"], "stage": trace["final_stage"], "code": trace["final_reason_code"], "counts": trace["counts"]},
            passed,
            "info" if passed else "critical",
            [] if passed else ["Enforcement stop either lacked explanation or performed downstream work."],
            trace,
        )
    finally:
        close_conn(conn, db_path)


def scenario_http_policy_block_reconstructs_policy_boundary() -> EvidenceScenarioResult:
    conn, db_path = fresh_conn(); session_id = "BD-HTTP"; task_id = "BD-HTTP-TASK"
    try:
        prepare_allowed(conn, session_id=session_id, task_id=task_id)
        register_api_endpoint_policy(conn, policy_id="POL-BD", allowed_host="api.example.com", allowed_path_prefixes=["/v1"], allowed_methods=["POST"])
        request = realish_request(request_id="REQ-BD-HTTP", session_id=session_id, task_id=task_id, endpoint="https://api.example.com/v10/items")
        result = call_controlled_external_api(conn, request=request, token=issue_api_token(conn, task_id=task_id), transport=transport_success)
        trace = build_task_trace(conn, task_id)
        api_event = [e for e in trace["events"] if e["type"] == "external_api_call"][-1]
        http_meta = api_event["evaluation"]["http_policy"]
        secret_meta = api_event["evaluation"]["secret_resolution"]
        passed = (
            result.decision == "blocked"
            and result.stage == "http_policy"
            and trace["final_status"] == "blocked"
            and trace["final_stage"] == "http_policy"
            and trace["final_reason_code"] == "OK_ACTION_READY"
            and http_meta["status"] == "blocked"
            and "not allowlisted" in http_meta["reason"]
            and secret_meta["status"] == "not_required"
        )
        return EvidenceScenarioResult(
            "http_policy_block_reconstructs_policy_boundary",
            "A policy-denied HTTP action must show that core guards passed but HTTP Policy stopped before secret/transport.",
            {"status": "blocked", "stage": "http_policy", "http_policy": "blocked", "pipeline_code": "OK_ACTION_READY"},
            {"status": trace["final_status"], "stage": trace["final_stage"], "code": trace["final_reason_code"], "http_policy": http_meta, "secret": secret_meta},
            passed,
            "info" if passed else "high",
            [] if passed else ["HTTP policy boundary was not reconstructable from the audit event."],
            trace,
        )
    finally:
        close_conn(conn, db_path)


def scenario_secret_flow_reconstructs_without_leak() -> EvidenceScenarioResult:
    conn, db_path = fresh_conn(); session_id = "BD-SECRET"; task_id = "BD-SECRET-TASK"
    secret_value = "BD_SUPER_SECRET_VALUE_SHOULD_NOT_APPEAR"
    old_json = os.environ.get("GATEGRAPH_SECRET_PROVIDER_JSON")
    try:
        os.environ["GATEGRAPH_SECRET_PROVIDER_JSON"] = '{"BD_API_KEY":"' + secret_value + '"}'
        prepare_allowed(conn, session_id=session_id, task_id=task_id)
        register_api_endpoint_policy(conn, policy_id="POL-BD-SECRET", allowed_host="api.example.com", allowed_path_prefixes=["/v1"], allowed_methods=["POST"])
        register_env_secret_ref(conn, secret_ref_id="SEC-BD", secret_name="BD_API_KEY", allowed_endpoint_prefixes=["https://api.example.com/v1"], allowed_capabilities=["api_call"])
        request = realish_request(request_id="REQ-BD-SECRET", session_id=session_id, task_id=task_id, endpoint="https://api.example.com/v1/items", secret_ref_id="SEC-BD")
        result = call_controlled_external_api(conn, request=request, token=issue_api_token(conn, task_id=task_id), transport=transport_success)
        trace = build_task_trace(conn, task_id)
        api_event = [e for e in trace["events"] if e["type"] == "external_api_call"][-1]
        secret_meta = api_event["evaluation"]["secret_resolution"]
        leaked = contains_secret_value(trace, secret_value)
        passed = (
            result.decision == "completed"
            and trace["final_status"] == "completed"
            and trace["final_stage"] == "action_ready"
            and secret_meta["status"] == "resolved"
            and secret_meta["secret_ref_id"] == "SEC-BD"
            and secret_meta["secret_name"] == "BD_API_KEY"
            and not leaked
        )
        return EvidenceScenarioResult(
            "secret_flow_reconstructs_without_leak",
            "A secret-backed completed call must be explainable while keeping raw secret material out of trace/audit output.",
            {"status": "completed", "secret_status": "resolved", "secret_leaked": False},
            {"status": trace["final_status"], "stage": trace["final_stage"], "secret": secret_meta, "secret_leaked": leaked},
            passed,
            "info" if passed else "critical",
            [] if passed else ["Secret-backed flow leaked secret material or was not reconstructable."],
            trace,
        )
    finally:
        if old_json is None:
            os.environ.pop("GATEGRAPH_SECRET_PROVIDER_JSON", None)
        else:
            os.environ["GATEGRAPH_SECRET_PROVIDER_JSON"] = old_json
        close_conn(conn, db_path)


def main() -> int:
    run = EvidenceRunLog("block_d_audit_explain_evidence", started_at=__import__("audit_evidence").utc_now_iso())
    scenarios = [
        scenario_completed_flow_reconstructs_action_ready,
        scenario_enforcement_block_reconstructs_no_work,
        scenario_http_policy_block_reconstructs_policy_boundary,
        scenario_secret_flow_reconstructs_without_leak,
    ]
    for scenario in scenarios:
        result = scenario()
        run.add(result)
        mark = "✓" if result.passed else "✗"
        print(f"{mark} {result.test_name}: {result.actual}", flush=True)
    run.finish()
    path = run.write(LOG_DIR)
    print(f"\nBlock D Audit/Explain Evidence: {run.summary['passed']}/{run.summary['total']} passed", flush=True)
    print(f"Log: {path}", flush=True)
    return 0 if run.summary["failed"] == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
