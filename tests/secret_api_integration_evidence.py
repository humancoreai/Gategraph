"""
WHY: Secret/API evidence proves real integration seams stay behind Enforcement, Guards, and scoped secret refs.
INV: no real network calls are made; fake transport records whether auth material reached execution only after gates pass.
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
from src import runtime_guard, session_budget_guard, event_logger, capability_token, secret_provider
from src.external_api_adapter import ControlledAPIResponse, ExternalAPIRequest, call_controlled_external_api
from audit_evidence import EvidenceRunLog, EvidenceScenarioResult, collect_task_evidence

PROJECT_ROOT = Path(__file__).resolve().parents[1]
LOG_DIR = PROJECT_ROOT / "tests" / "logs"


def fresh_conn():
    tmp = tempfile.NamedTemporaryFile(prefix="gategraph_secret_api_", suffix=".db", delete=False)
    tmp.close()
    db_path = Path(tmp.name)
    init_db(db_path)
    conn = get_connection(db_path)
    ensure_runtime_schema(conn)
    ensure_pattern_schema(conn)
    session_budget_guard.ensure_session_budget_schema(conn)
    secret_provider.ensure_secret_schema(conn)
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
            event_id=f"EVT-SECRET-TOKEN-{task_id}",
            idempotency_key=f"secret-token-fixture:{task_id}",
            correlation_id=f"COR-SECRET-TOKEN-{task_id}",
            causation_id=None,
            event_type="test_token_fixture",
            task_id=task_id,
            actor_component="secret_api_test_fixture",
            input_data={"requested_capability": "api_call"},
            evaluation={"fixture": True},
            decision={"status": "allow", "final_capabilities": {"api_call": True}},
        )
        decision_id = f"DEC-SECRET-TOKEN-{task_id}"
        conn.execute(
            """
            INSERT OR IGNORE INTO decisions
              (decision_id, task_id, event_id, status, final_caps_json, reason, matched_rules_json, created_at)
            VALUES (?, ?, ?, 'allow', '{"api_call": true}', 'test fixture api token', '[]', datetime('now'))
            """,
            (decision_id, task_id, event.event_id),
        )
        return capability_token.issue_token(conn, decision_id, task_id, {"api_call": True})


def make_request(*, request_id: str, session_id: str, task_id: str, endpoint: str = "https://api.example.test/v1/search", secret_ref_id: str | None = "SEC-API-1") -> ExternalAPIRequest:
    return ExternalAPIRequest(
        request_id=request_id,
        session_id=session_id,
        task_id=task_id,
        actor_id="agent-secret-api",
        endpoint=endpoint,
        method="POST",
        payload_summary="redacted integration payload",
        projected_cost_units=1,
        timeout_ms=100,
        mock_behavior="success",
        requested_capability="api_call",
        secret_ref_id=secret_ref_id,
    )


def register_ref(conn, *, active: bool = True) -> None:
    secret_provider.register_env_secret_ref(
        conn,
        secret_ref_id="SEC-API-1",
        secret_name="TEST_API_KEY",
        allowed_endpoint_prefixes=["https://api.example.test/v1/"],
        allowed_capabilities=["api_call"],
        active=active,
    )


def scenario_secret_resolved_only_after_guards() -> EvidenceScenarioResult:
    conn, db_path = fresh_conn(); session_id = "SEC-API-OK"; task_id = "SEC-API-OK-TASK"
    old_env = os.environ.get("GATEGRAPH_SECRET_PROVIDER_JSON")
    calls = []
    try:
        os.environ["GATEGRAPH_SECRET_PROVIDER_JSON"] = '{"TEST_API_KEY":"super-secret-test-value"}'
        prepare_allowed(conn, session_id=session_id, task_id=task_id)
        register_ref(conn)

        def fake_transport(request: ExternalAPIRequest, headers: Mapping[str, str]) -> ControlledAPIResponse:
            calls.append(dict(headers))
            return ControlledAPIResponse(200, "controlled transport success")

        result = call_controlled_external_api(conn, request=make_request(request_id="REQ-SEC-API-OK", session_id=session_id, task_id=task_id), token=issue_api_token(conn, task_id=task_id), transport=fake_transport)
        evidence = collect_task_evidence(conn, task_id)
        api_event = [e for e in evidence["events"] if e["type"] == "external_api_call"][0]
        text_dump = str(api_event)
        passed = (
            result.decision == "completed"
            and result.stage == "action_ready"
            and len(calls) == 1
            and calls[0].get("Authorization") == "Bearer super-secret-test-value"
            and "super-secret-test-value" not in text_dump
            and api_event["evaluation"]["secret_resolution"]["status"] == "resolved"
        )
        return EvidenceScenarioResult("secret_resolved_only_after_guards", "Scoped env secret reaches transport only after all guards pass and is not logged.", {"decision": "completed", "secret_logged": False, "transport_calls": 1}, {"decision": result.decision, "stage": result.stage, "secret_logged": "super-secret-test-value" in text_dump, "transport_calls": len(calls)}, passed, "info" if passed else "critical", [] if passed else ["Secret integration path was not gated or leaked secret material."], evidence)
    finally:
        if old_env is None:
            os.environ.pop("GATEGRAPH_SECRET_PROVIDER_JSON", None)
        else:
            os.environ["GATEGRAPH_SECRET_PROVIDER_JSON"] = old_env
        close_conn(conn, db_path)


def scenario_missing_secret_blocks_before_transport() -> EvidenceScenarioResult:
    conn, db_path = fresh_conn(); session_id = "SEC-API-MISSING"; task_id = "SEC-API-MISSING-TASK"
    old_env = os.environ.pop("GATEGRAPH_SECRET_PROVIDER_JSON", None)
    calls = []
    try:
        prepare_allowed(conn, session_id=session_id, task_id=task_id)
        register_ref(conn)

        def fake_transport(request: ExternalAPIRequest, headers: Mapping[str, str]) -> ControlledAPIResponse:
            calls.append(dict(headers))
            return ControlledAPIResponse(200, "should not run")

        result = call_controlled_external_api(conn, request=make_request(request_id="REQ-SEC-API-MISSING", session_id=session_id, task_id=task_id), token=issue_api_token(conn, task_id=task_id), transport=fake_transport)
        evidence = collect_task_evidence(conn, task_id)
        passed = result.decision == "blocked" and result.stage == "secret_provider" and len(calls) == 0 and "unavailable" in result.response_summary
        return EvidenceScenarioResult("missing_secret_blocks_before_transport", "Missing secret value must fail closed before transport execution.", {"decision": "blocked", "stage": "secret_provider", "transport_calls": 0}, {"decision": result.decision, "stage": result.stage, "response": result.response_summary, "transport_calls": len(calls)}, passed, "info" if passed else "critical", [] if passed else ["Missing secret did not block before transport."], evidence)
    finally:
        if old_env is not None:
            os.environ["GATEGRAPH_SECRET_PROVIDER_JSON"] = old_env
        close_conn(conn, db_path)


def scenario_endpoint_scope_mismatch_blocks() -> EvidenceScenarioResult:
    conn, db_path = fresh_conn(); session_id = "SEC-API-SCOPE"; task_id = "SEC-API-SCOPE-TASK"
    old_env = os.environ.get("GATEGRAPH_SECRET_PROVIDER_JSON")
    calls = []
    try:
        os.environ["GATEGRAPH_SECRET_PROVIDER_JSON"] = '{"TEST_API_KEY":"super-secret-test-value"}'
        prepare_allowed(conn, session_id=session_id, task_id=task_id)
        register_ref(conn)

        def fake_transport(request: ExternalAPIRequest, headers: Mapping[str, str]) -> ControlledAPIResponse:
            calls.append(dict(headers))
            return ControlledAPIResponse(200, "should not run")

        result = call_controlled_external_api(conn, request=make_request(request_id="REQ-SEC-API-SCOPE", session_id=session_id, task_id=task_id, endpoint="https://evil.example.test/v1/search"), token=issue_api_token(conn, task_id=task_id), transport=fake_transport)
        evidence = collect_task_evidence(conn, task_id)
        passed = result.decision == "blocked" and result.stage == "secret_provider" and len(calls) == 0 and "scope mismatch" in result.response_summary
        return EvidenceScenarioResult("endpoint_scope_mismatch_blocks", "Secret refs must be bound to allowed endpoint prefixes.", {"decision": "blocked", "stage": "secret_provider", "transport_calls": 0}, {"decision": result.decision, "stage": result.stage, "response": result.response_summary, "transport_calls": len(calls)}, passed, "info" if passed else "critical", [] if passed else ["Endpoint scope mismatch did not block."], evidence)
    finally:
        if old_env is None:
            os.environ.pop("GATEGRAPH_SECRET_PROVIDER_JSON", None)
        else:
            os.environ["GATEGRAPH_SECRET_PROVIDER_JSON"] = old_env
        close_conn(conn, db_path)


def scenario_no_token_blocks_before_secret_resolution() -> EvidenceScenarioResult:
    conn, db_path = fresh_conn(); session_id = "SEC-API-NO-TOKEN"; task_id = "SEC-API-NO-TOKEN-TASK"
    old_env = os.environ.get("GATEGRAPH_SECRET_PROVIDER_JSON")
    calls = []
    try:
        os.environ["GATEGRAPH_SECRET_PROVIDER_JSON"] = '{"TEST_API_KEY":"super-secret-test-value"}'
        prepare_allowed(conn, session_id=session_id, task_id=task_id)
        register_ref(conn)

        def fake_transport(request: ExternalAPIRequest, headers: Mapping[str, str]) -> ControlledAPIResponse:
            calls.append(dict(headers))
            return ControlledAPIResponse(200, "should not run")

        result = call_controlled_external_api(conn, request=make_request(request_id="REQ-SEC-API-NO-TOKEN", session_id=session_id, task_id=task_id), token=None, transport=fake_transport)
        evidence = collect_task_evidence(conn, task_id)
        api_event = [e for e in evidence["events"] if e["type"] == "external_api_call"][0]
        passed = result.decision == "blocked" and result.stage == "enforcement" and len(calls) == 0 and api_event["evaluation"]["secret_resolution"]["status"] == "not_resolved"
        return EvidenceScenarioResult("no_token_blocks_before_secret_resolution", "Authorization failure must stop before secret resolution and transport.", {"decision": "blocked", "stage": "enforcement", "transport_calls": 0}, {"decision": result.decision, "stage": result.stage, "transport_calls": len(calls), "secret_status": api_event["evaluation"]["secret_resolution"]["status"]}, passed, "info" if passed else "critical", [] if passed else ["No-token path resolved secret or touched transport."], evidence)
    finally:
        if old_env is None:
            os.environ.pop("GATEGRAPH_SECRET_PROVIDER_JSON", None)
        else:
            os.environ["GATEGRAPH_SECRET_PROVIDER_JSON"] = old_env
        close_conn(conn, db_path)


def main() -> int:
    run_id = datetime.now(timezone.utc).strftime("secret_api_integration_evidence_%Y%m%d_%H%M%S")
    log = EvidenceRunLog(run_id=run_id, started_at=datetime.now(timezone.utc).isoformat())
    scenarios = [
        scenario_secret_resolved_only_after_guards,
        scenario_missing_secret_blocks_before_transport,
        scenario_endpoint_scope_mismatch_blocks,
        scenario_no_token_blocks_before_secret_resolution,
    ]
    for scenario in scenarios:
        result = scenario()
        log.add(result)
        mark = "✓" if result.passed else "✗"
        print(f"{mark} {result.test_name}: {result.actual}")
    log.finish()
    out = log.write(LOG_DIR)
    print("\nSECRET/API INTEGRATION EVIDENCE REPORT")
    print(f"Log: {out}")
    print(f"Summary: {log.summary}")
    return 0 if log.summary["failed"] == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
