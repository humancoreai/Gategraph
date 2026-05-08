"""
WHY: Block B evidence probes edge cases around secrets, HTTP policy boundaries, and token stop precedence.
INV: no secret value enters audit; HTTP allowlists are exact/boundary-aware; combined token failures stay fail-closed.
"""
from __future__ import annotations

import json
import os
import sys
import tempfile
from dataclasses import replace
from pathlib import Path
from typing import Mapping

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.database import get_connection, init_db, seed_rules, ensure_runtime_schema, ensure_pattern_schema
from src import runtime_guard, session_budget_guard, event_logger, capability_token, secret_provider, http_policy
from src.enforcement import enforce
from src.external_api_adapter import ControlledAPIResponse, ExternalAPIRequest, call_controlled_external_api
from audit_evidence import EvidenceRunLog, EvidenceScenarioResult, collect_task_evidence, utc_now_iso

PROJECT_ROOT = Path(__file__).resolve().parents[1]
LOG_DIR = PROJECT_ROOT / "tests" / "logs"
SECRET_VALUE = "super-secret-block-b-value"


def fresh_conn():
    tmp = tempfile.NamedTemporaryFile(prefix="gategraph_block_b_", suffix=".db", delete=False)
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
            event_id=f"EVT-BLOCK-B-TOKEN-{task_id}",
            idempotency_key=f"block-b-token-fixture:{task_id}",
            correlation_id=f"COR-BLOCK-B-TOKEN-{task_id}",
            causation_id=None,
            event_type="test_token_fixture",
            task_id=task_id,
            actor_component="block_b_test_fixture",
            input_data={"requested_capability": "api_call"},
            evaluation={"fixture": True},
            decision={"status": "allow", "final_capabilities": {"api_call": True}},
        )
        decision_id = f"DEC-BLOCK-B-TOKEN-{task_id}"
        conn.execute(
            """
            INSERT OR IGNORE INTO decisions
              (decision_id, task_id, event_id, status, final_caps_json, reason, matched_rules_json, created_at)
            VALUES (?, ?, ?, 'allow', '{"api_call": true}', 'test fixture api token', '[]', datetime('now'))
            """,
            (decision_id, task_id, event.event_id),
        )
        return capability_token.issue_token(conn, decision_id, task_id, {"api_call": True})


def register_secret(conn, *, prefixes=None, active=True) -> None:
    secret_provider.register_env_secret_ref(
        conn,
        secret_ref_id="SEC-BLOCK-B",
        secret_name="BLOCK_B_API_KEY",
        allowed_endpoint_prefixes=prefixes or ["https://api.example.test/v1/"],
        allowed_capabilities=["api_call"],
        active=active,
    )


def register_policy(conn, *, host="api.example.test", prefixes=None, methods=None, active=True) -> None:
    http_policy.register_api_endpoint_policy(
        conn,
        policy_id="POL-BLOCK-B",
        allowed_host=host,
        allowed_path_prefixes=prefixes or ["/v1/"],
        allowed_methods=methods or ["POST"],
        active=active,
    )


def make_request(*, request_id: str, session_id: str, task_id: str, endpoint="https://api.example.test/v1/search", method="POST") -> ExternalAPIRequest:
    return ExternalAPIRequest(
        request_id=request_id,
        session_id=session_id,
        task_id=task_id,
        actor_id="agent-block-b",
        endpoint=endpoint,
        method=method,
        payload_summary="redacted block b payload",
        projected_cost_units=1,
        timeout_ms=100,
        mock_behavior="success",
        requested_capability="api_call",
        secret_ref_id="SEC-BLOCK-B",
    )


def run_api(conn, req: ExternalAPIRequest, token, calls):
    def fake_transport(request: ExternalAPIRequest, headers: Mapping[str, str]) -> ControlledAPIResponse:
        calls.append(dict(headers))
        return ControlledAPIResponse(200, "block b transport success")
    return call_controlled_external_api(conn, request=req, token=token, transport=fake_transport)


def with_secret_env(fn):
    old_json = os.environ.get("GATEGRAPH_SECRET_PROVIDER_JSON")
    old_direct = os.environ.get("GATEGRAPH_SECRET_BLOCK_B_API_KEY")
    try:
        os.environ["GATEGRAPH_SECRET_PROVIDER_JSON"] = json.dumps({"BLOCK_B_API_KEY": SECRET_VALUE})
        os.environ.pop("GATEGRAPH_SECRET_BLOCK_B_API_KEY", None)
        return fn()
    finally:
        if old_json is None:
            os.environ.pop("GATEGRAPH_SECRET_PROVIDER_JSON", None)
        else:
            os.environ["GATEGRAPH_SECRET_PROVIDER_JSON"] = old_json
        if old_direct is None:
            os.environ.pop("GATEGRAPH_SECRET_BLOCK_B_API_KEY", None)
        else:
            os.environ["GATEGRAPH_SECRET_BLOCK_B_API_KEY"] = old_direct


def scenario_secret_value_not_in_audit() -> EvidenceScenarioResult:
    def body():
        conn, db = fresh_conn(); session_id="BB-SECRET-LOG"; task_id="BB-SECRET-LOG-TASK"; calls=[]
        try:
            prepare_allowed(conn, session_id=session_id, task_id=task_id); register_secret(conn); register_policy(conn)
            token = issue_api_token(conn, task_id=task_id)
            result = run_api(conn, make_request(request_id="REQ-BB-SECRET-LOG", session_id=session_id, task_id=task_id), token, calls)
            evidence = collect_task_evidence(conn, task_id)
            blob = json.dumps(evidence, sort_keys=True)
            passed = result.decision == "completed" and SECRET_VALUE not in blob and len(calls) == 1 and calls[0].get("Authorization") == f"Bearer {SECRET_VALUE}"
            return EvidenceScenarioResult("secret_value_not_in_audit", "Secret reaches transport but raw value is absent from audit/evidence.", {"decision":"completed", "secret_in_audit": False}, {"decision":result.decision, "secret_in_audit": SECRET_VALUE in blob, "transport_calls":len(calls)}, passed, "info" if passed else "critical", [] if passed else ["Secret value leaked into audit/evidence or did not reach transport."], evidence)
        finally:
            close_conn(conn, db)
    return with_secret_env(body)


def scenario_policy_block_prevents_secret_resolution() -> EvidenceScenarioResult:
    def body():
        conn, db = fresh_conn(); session_id="BB-POL-BEFORE-SEC"; task_id="BB-POL-BEFORE-SEC-TASK"; calls=[]
        try:
            prepare_allowed(conn, session_id=session_id, task_id=task_id); register_secret(conn); register_policy(conn)
            token = issue_api_token(conn, task_id=task_id)
            req = make_request(request_id="REQ-BB-POL-BEFORE-SEC", session_id=session_id, task_id=task_id, endpoint="https://evil.example.test/v1/search")
            result = run_api(conn, req, token, calls)
            evidence = collect_task_evidence(conn, task_id)
            api_event = [e for e in evidence["events"] if e["type"] == "external_api_call"][0]
            secret_status = api_event["evaluation"]["secret_resolution"]["status"]
            passed = result.decision == "blocked" and result.stage == "http_policy" and secret_status == "not_resolved" and SECRET_VALUE not in json.dumps(evidence) and len(calls) == 0
            return EvidenceScenarioResult("policy_block_prevents_secret_resolution", "HTTP policy denial happens before secret provider/transport.", {"stage":"http_policy", "secret_status":"not_resolved"}, {"decision":result.decision, "stage":result.stage, "secret_status":secret_status, "transport_calls":len(calls)}, passed, "info" if passed else "critical", [] if passed else ["Secret was resolved before HTTP policy or transport was reached."], evidence)
        finally:
            close_conn(conn, db)
    return with_secret_env(body)


def scenario_subdomain_not_implicitly_allowed() -> EvidenceScenarioResult:
    def body():
        conn, db = fresh_conn(); session_id="BB-SUBDOMAIN"; task_id="BB-SUBDOMAIN-TASK"; calls=[]
        try:
            prepare_allowed(conn, session_id=session_id, task_id=task_id); register_secret(conn, prefixes=["https://sub.api.example.test/v1/"]); register_policy(conn)
            token = issue_api_token(conn, task_id=task_id)
            req = make_request(request_id="REQ-BB-SUBDOMAIN", session_id=session_id, task_id=task_id, endpoint="https://sub.api.example.test/v1/search")
            result = run_api(conn, req, token, calls)
            evidence = collect_task_evidence(conn, task_id)
            passed = result.decision == "blocked" and result.stage == "http_policy" and len(calls) == 0
            return EvidenceScenarioResult("subdomain_not_implicitly_allowed", "Allowlisted parent host does not automatically allow subdomains.", {"decision":"blocked", "stage":"http_policy"}, {"decision":result.decision, "stage":result.stage, "response":result.response_summary}, passed, "info" if passed else "critical", [] if passed else ["Subdomain was allowed by parent host policy."], evidence)
        finally:
            close_conn(conn, db)
    return with_secret_env(body)


def scenario_wildcard_host_policy_rejected() -> EvidenceScenarioResult:
    conn, db = fresh_conn()
    try:
        try:
            register_policy(conn, host="*.example.test")
            rejected = False
            detail = "accepted"
        except ValueError as exc:
            rejected = True
            detail = str(exc)
        return EvidenceScenarioResult("wildcard_host_policy_rejected", "Wildcard hosts are rejected rather than interpreted implicitly.", {"rejected": True}, {"rejected": rejected, "detail": detail}, rejected, "info" if rejected else "critical", [] if rejected else ["Wildcard host policy was accepted."], {})
    finally:
        close_conn(conn, db)


def scenario_path_prefix_boundary_blocks_neighbor() -> EvidenceScenarioResult:
    def body():
        conn, db = fresh_conn(); session_id="BB-PATH-BOUNDARY"; task_id="BB-PATH-BOUNDARY-TASK"; calls=[]
        try:
            prepare_allowed(conn, session_id=session_id, task_id=task_id); register_secret(conn, prefixes=["https://api.example.test/v10/search"]); register_policy(conn, prefixes=["/v1"])
            token = issue_api_token(conn, task_id=task_id)
            req = make_request(request_id="REQ-BB-PATH-BOUNDARY", session_id=session_id, task_id=task_id, endpoint="https://api.example.test/v10/search")
            result = run_api(conn, req, token, calls)
            evidence = collect_task_evidence(conn, task_id)
            passed = result.decision == "blocked" and result.stage == "http_policy" and len(calls) == 0
            return EvidenceScenarioResult("path_prefix_boundary_blocks_neighbor", "Policy prefix /v1 must not allow /v10 or /v1evil.", {"decision":"blocked", "stage":"http_policy"}, {"decision":result.decision, "stage":result.stage, "response":result.response_summary}, passed, "info" if passed else "critical", [] if passed else ["Boundary-unsafe prefix matching allowed neighboring path."], evidence)
        finally:
            close_conn(conn, db)
    return with_secret_env(body)


def scenario_lowercase_method_normalized() -> EvidenceScenarioResult:
    def body():
        conn, db = fresh_conn(); session_id="BB-METHOD-CASE"; task_id="BB-METHOD-CASE-TASK"; calls=[]
        try:
            prepare_allowed(conn, session_id=session_id, task_id=task_id); register_secret(conn); register_policy(conn, methods=["POST"])
            token = issue_api_token(conn, task_id=task_id)
            req = make_request(request_id="REQ-BB-METHOD-CASE", session_id=session_id, task_id=task_id, method="post")
            result = run_api(conn, req, token, calls)
            evidence = collect_task_evidence(conn, task_id)
            passed = result.decision == "completed" and len(calls) == 1
            return EvidenceScenarioResult("lowercase_method_normalized", "HTTP methods are normalized before policy evaluation.", {"decision":"completed"}, {"decision":result.decision, "stage":result.stage, "transport_calls":len(calls)}, passed, "info" if passed else "medium", [] if passed else ["Lowercase method was not normalized."], evidence)
        finally:
            close_conn(conn, db)
    return with_secret_env(body)


def scenario_expired_and_revoked_token_stays_fail_closed() -> EvidenceScenarioResult:
    conn, db = fresh_conn(); task_id="BB-EXPIRED-REVOKED"
    try:
        with conn:
            conn.execute("""
            INSERT OR IGNORE INTO tasks
              (task_id, task_type, capabilities, input_source, data_sensitivity, secrets_involved, created_at)
            VALUES (?, 'external_api_call', '["api_call"]', 'local', 'internal', 0, datetime('now'))
            """, (task_id,))
            event = event_logger.log_event(conn, event_id="EVT-BB-EXPIRED-REVOKED", idempotency_key="bb-expired-revoked", correlation_id="COR-BB-EXPIRED-REVOKED", causation_id=None, event_type="test_token_fixture", task_id=task_id, actor_component="block_b_test_fixture", input_data={}, evaluation={}, decision={"status":"allow", "final_capabilities":{"api_call": True}})
            decision_id="DEC-BB-EXPIRED-REVOKED"
            conn.execute("""
            INSERT OR IGNORE INTO decisions
              (decision_id, task_id, event_id, status, final_caps_json, reason, matched_rules_json, created_at)
            VALUES (?, ?, ?, 'allow', '{"api_call": true}', 'expired revoked fixture', '[]', datetime('now'))
            """, (decision_id, task_id, event.event_id))
            token = capability_token.issue_expired_token(conn, decision_id, task_id, {"api_call": True})
            conn.execute("UPDATE capability_tokens SET revoked=1 WHERE token_id=?", (token.token_id,))
        result = enforce(conn, token, "api_call", task_id, "COR-BB-EXPIRED-REVOKED")
        evidence = collect_task_evidence(conn, task_id)
        passed = not result.allowed and "expired" in result.reason
        return EvidenceScenarioResult("expired_and_revoked_token_stays_fail_closed", "Combined expiry+revocation remains blocked with deterministic expiry-first reason.", {"allowed": False, "reason_contains":"expired"}, {"allowed": result.allowed, "reason": result.reason}, passed, "info" if passed else "critical", [] if passed else ["Expired+revoked token did not fail closed deterministically."], evidence)
    finally:
        close_conn(conn, db)


def main() -> int:
    run = EvidenceRunLog(run_id="security_finesse_evidence_v0_8_13", started_at=utc_now_iso())
    scenarios = [
        scenario_secret_value_not_in_audit,
        scenario_policy_block_prevents_secret_resolution,
        scenario_subdomain_not_implicitly_allowed,
        scenario_wildcard_host_policy_rejected,
        scenario_path_prefix_boundary_blocks_neighbor,
        scenario_lowercase_method_normalized,
        scenario_expired_and_revoked_token_stays_fail_closed,
    ]
    for fn in scenarios:
        result = fn()
        run.add(result)
        print(("✓" if result.passed else "✗"), result.test_name, result.actual)
    run.finish()
    path = run.write(LOG_DIR)
    print(f"\nEvidence written: {path}")
    print(f"Result: {run.summary['passed']}/{run.summary['total']} passed")
    return 0 if run.summary["failed"] == 0 else 1


if __name__ == "__main__":
    os._exit(main())
