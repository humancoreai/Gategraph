"""
WHY: HTTP policy evidence proves real outbound endpoints are fail-closed unless allowlisted.
INV: Enforcement and Guards still run before policy; transport runs only after policy + secret resolution pass.
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
from src import runtime_guard, session_budget_guard, event_logger, capability_token, secret_provider, http_policy
from src.external_api_adapter import ControlledAPIResponse, ExternalAPIRequest, call_controlled_external_api
from audit_evidence import EvidenceRunLog, EvidenceScenarioResult, collect_task_evidence

PROJECT_ROOT = Path(__file__).resolve().parents[1]
LOG_DIR = PROJECT_ROOT / "tests" / "logs"


def fresh_conn():
    tmp = tempfile.NamedTemporaryFile(prefix="gategraph_http_policy_", suffix=".db", delete=False)
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


def prepare_allowed(conn, *, session_id: str, task_id: str) -> None:
    session_budget_guard.create_session_budget(conn, session_id=session_id, max_session_cost_units=100, max_session_tasks=20, max_agent_cost_units=100)
    runtime_guard.create_budget(conn, task_id=task_id, max_steps=10, max_cost_units=100, repeated_action_limit=10)


def issue_api_token(conn, *, task_id: str):
    with conn:
        conn.execute(
            """
            INSERT OR IGNORE INTO tasks
              (task_id, task_type, capabilities, input_source, data_sensitivity, secrets_involved, created_at)
            VALUES (?, 'external_api_call', '["api_call"]', 'local', 'internal', 1, datetime('now'))
            """,
            (task_id,),
        )
        event = event_logger.log_event(
            conn,
            event_id=f"EVT-HTTP-POL-TOKEN-{task_id}",
            idempotency_key=f"http-policy-token-fixture:{task_id}",
            correlation_id=f"COR-HTTP-POL-TOKEN-{task_id}",
            causation_id=None,
            event_type="test_token_fixture",
            task_id=task_id,
            actor_component="http_policy_test_fixture",
            input_data={"requested_capability": "api_call"},
            evaluation={"fixture": True},
            decision={"status": "allow", "final_capabilities": {"api_call": True}},
        )
        decision_id = f"DEC-HTTP-POL-TOKEN-{task_id}"
        conn.execute(
            """
            INSERT OR IGNORE INTO decisions
              (decision_id, task_id, event_id, status, final_caps_json, reason, matched_rules_json, created_at)
            VALUES (?, ?, ?, 'allow', '{"api_call": true}', 'test fixture api token', '[]', datetime('now'))
            """,
            (decision_id, task_id, event.event_id),
        )
        return capability_token.issue_token(conn, decision_id, task_id, {"api_call": True})


def register_secret(conn) -> None:
    secret_provider.register_env_secret_ref(
        conn,
        secret_ref_id="SEC-HTTP-POLICY",
        secret_name="TEST_API_KEY",
        allowed_endpoint_prefixes=["https://api.example.test/v1/"],
        allowed_capabilities=["api_call"],
    )


def register_policy(conn, *, active: bool = True, methods=None) -> None:
    http_policy.register_api_endpoint_policy(
        conn,
        policy_id="POL-HTTP-EXAMPLE",
        allowed_host="api.example.test",
        allowed_path_prefixes=["/v1/"],
        allowed_methods=methods or ["POST"],
        active=active,
    )


def make_request(*, request_id: str, session_id: str, task_id: str, endpoint: str = "https://api.example.test/v1/search", method: str = "POST") -> ExternalAPIRequest:
    return ExternalAPIRequest(
        request_id=request_id,
        session_id=session_id,
        task_id=task_id,
        actor_id="agent-http-policy",
        endpoint=endpoint,
        method=method,
        payload_summary="redacted policy payload",
        projected_cost_units=1,
        timeout_ms=100,
        mock_behavior="success",
        requested_capability="api_call",
        secret_ref_id="SEC-HTTP-POLICY",
    )


def _run(request: ExternalAPIRequest, conn, task_id: str, calls):
    def fake_transport(req: ExternalAPIRequest, headers: Mapping[str, str]) -> ControlledAPIResponse:
        calls.append(dict(headers))
        return ControlledAPIResponse(200, "policy transport success")
    return call_controlled_external_api(conn, request=request, token=issue_api_token(conn, task_id=task_id), transport=fake_transport)


def scenario_allowlisted_https_executes() -> EvidenceScenarioResult:
    conn, db_path = fresh_conn(); session_id = "HTTP-POL-OK"; task_id = "HTTP-POL-OK-TASK"; calls = []
    old_env = os.environ.get("GATEGRAPH_SECRET_PROVIDER_JSON")
    try:
        os.environ["GATEGRAPH_SECRET_PROVIDER_JSON"] = '{"TEST_API_KEY":"secret-for-policy"}'
        prepare_allowed(conn, session_id=session_id, task_id=task_id); register_secret(conn); register_policy(conn)
        result = _run(make_request(request_id="REQ-HTTP-POL-OK", session_id=session_id, task_id=task_id), conn, task_id, calls)
        evidence = collect_task_evidence(conn, task_id)
        api_event = [e for e in evidence["events"] if e["type"] == "external_api_call"][0]
        passed = result.decision == "completed" and len(calls) == 1 and api_event["evaluation"]["http_policy"]["status"] == "allowed"
        return EvidenceScenarioResult("allowlisted_https_executes", "Allowlisted HTTPS host/path/method may reach transport after gates.", {"decision": "completed", "transport_calls": 1}, {"decision": result.decision, "stage": result.stage, "transport_calls": len(calls)}, passed, "info" if passed else "critical", [] if passed else ["Allowlisted policy path did not execute cleanly."], evidence)
    finally:
        if old_env is None: os.environ.pop("GATEGRAPH_SECRET_PROVIDER_JSON", None)
        else: os.environ["GATEGRAPH_SECRET_PROVIDER_JSON"] = old_env
        close_conn(conn, db_path)


def scenario_unallowlisted_host_blocks() -> EvidenceScenarioResult:
    conn, db_path = fresh_conn(); session_id = "HTTP-POL-HOST"; task_id = "HTTP-POL-HOST-TASK"; calls = []
    old_env = os.environ.get("GATEGRAPH_SECRET_PROVIDER_JSON")
    try:
        os.environ["GATEGRAPH_SECRET_PROVIDER_JSON"] = '{"TEST_API_KEY":"secret-for-policy"}'
        prepare_allowed(conn, session_id=session_id, task_id=task_id); register_secret(conn); register_policy(conn)
        req = make_request(request_id="REQ-HTTP-POL-HOST", session_id=session_id, task_id=task_id, endpoint="https://evil.example.test/v1/search")
        result = _run(req, conn, task_id, calls)
        evidence = collect_task_evidence(conn, task_id)
        passed = result.decision == "blocked" and result.stage == "http_policy" and len(calls) == 0 and "not allowlisted" in result.response_summary
        return EvidenceScenarioResult("unallowlisted_host_blocks", "Unknown host must fail closed before secret resolution/transport.", {"decision": "blocked", "stage": "http_policy", "transport_calls": 0}, {"decision": result.decision, "stage": result.stage, "response": result.response_summary, "transport_calls": len(calls)}, passed, "info" if passed else "critical", [] if passed else ["Unallowlisted host reached transport or wrong stage."], evidence)
    finally:
        if old_env is None: os.environ.pop("GATEGRAPH_SECRET_PROVIDER_JSON", None)
        else: os.environ["GATEGRAPH_SECRET_PROVIDER_JSON"] = old_env
        close_conn(conn, db_path)


def scenario_method_mismatch_blocks() -> EvidenceScenarioResult:
    conn, db_path = fresh_conn(); session_id = "HTTP-POL-METHOD"; task_id = "HTTP-POL-METHOD-TASK"; calls = []
    old_env = os.environ.get("GATEGRAPH_SECRET_PROVIDER_JSON")
    try:
        os.environ["GATEGRAPH_SECRET_PROVIDER_JSON"] = '{"TEST_API_KEY":"secret-for-policy"}'
        prepare_allowed(conn, session_id=session_id, task_id=task_id); register_secret(conn); register_policy(conn, methods=["GET"])
        req = make_request(request_id="REQ-HTTP-POL-METHOD", session_id=session_id, task_id=task_id, method="POST")
        result = _run(req, conn, task_id, calls)
        evidence = collect_task_evidence(conn, task_id)
        passed = result.decision == "blocked" and result.stage == "http_policy" and len(calls) == 0
        return EvidenceScenarioResult("method_mismatch_blocks", "Method not present in policy must fail closed.", {"decision": "blocked", "stage": "http_policy", "transport_calls": 0}, {"decision": result.decision, "stage": result.stage, "response": result.response_summary, "transport_calls": len(calls)}, passed, "info" if passed else "critical", [] if passed else ["Method mismatch did not block."], evidence)
    finally:
        if old_env is None: os.environ.pop("GATEGRAPH_SECRET_PROVIDER_JSON", None)
        else: os.environ["GATEGRAPH_SECRET_PROVIDER_JSON"] = old_env
        close_conn(conn, db_path)


def scenario_http_scheme_blocks() -> EvidenceScenarioResult:
    conn, db_path = fresh_conn(); session_id = "HTTP-POL-SCHEME"; task_id = "HTTP-POL-SCHEME-TASK"; calls = []
    old_env = os.environ.get("GATEGRAPH_SECRET_PROVIDER_JSON")
    try:
        os.environ["GATEGRAPH_SECRET_PROVIDER_JSON"] = '{"TEST_API_KEY":"secret-for-policy"}'
        prepare_allowed(conn, session_id=session_id, task_id=task_id); register_secret(conn); register_policy(conn)
        req = make_request(request_id="REQ-HTTP-POL-SCHEME", session_id=session_id, task_id=task_id, endpoint="http://api.example.test/v1/search")
        result = _run(req, conn, task_id, calls)
        evidence = collect_task_evidence(conn, task_id)
        passed = result.decision == "blocked" and result.stage == "http_policy" and len(calls) == 0 and "scheme" in result.response_summary
        return EvidenceScenarioResult("http_scheme_blocks", "Plain HTTP must fail closed even for otherwise matching host/path.", {"decision": "blocked", "stage": "http_policy", "transport_calls": 0}, {"decision": result.decision, "stage": result.stage, "response": result.response_summary, "transport_calls": len(calls)}, passed, "info" if passed else "critical", [] if passed else ["Plain HTTP did not block."], evidence)
    finally:
        if old_env is None: os.environ.pop("GATEGRAPH_SECRET_PROVIDER_JSON", None)
        else: os.environ["GATEGRAPH_SECRET_PROVIDER_JSON"] = old_env
        close_conn(conn, db_path)


def main() -> int:
    run_id = datetime.now(timezone.utc).strftime("http_policy_evidence_%Y%m%d_%H%M%S")
    log = EvidenceRunLog(run_id=run_id, started_at=datetime.now(timezone.utc).isoformat())
    for scenario in [scenario_allowlisted_https_executes, scenario_unallowlisted_host_blocks, scenario_method_mismatch_blocks, scenario_http_scheme_blocks]:
        result = scenario(); log.add(result)
        mark = "✓" if result.passed else "✗"
        print(f"{mark} {result.test_name}: {result.actual}")
    log.finish(); out = log.write(LOG_DIR)
    print("\nHTTP POLICY EVIDENCE REPORT")
    print(f"Log: {out}")
    print(f"Summary: {log.summary}")
    return 0 if log.summary["failed"] == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
