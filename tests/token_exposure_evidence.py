"""
WHY: v0.11.9 proves observability-safe governance boundaries for tokens, auth headers and secrets.
INV: audit/explain/monitoring outputs may reference ids and one-way hashes only; raw sensitive material is redacted.
SEC: Base64 is not protection. Unexpected token/header formats fail closed instead of being serialized.
"""
from __future__ import annotations

import base64
import json
import os
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src import event_logger
from src.database import get_connection, init_db, seed_rules
from src.explain_trace import build_task_trace, contains_secret_value
from src.external_api_adapter import ExternalAPIRequest, ControlledAPIResponse, call_controlled_external_api
from src import capability_token, runtime_guard, secret_provider, session_budget_guard
from src.http_policy import register_api_endpoint_policy
from src.monitoring_export import build_monitoring_export
from src.security.token_redaction import RedactionError, redact_authorization_header, redact_token_value

SECRET_VALUE = "V0115_SUPER_SECRET_VALUE_SHOULD_NOT_APPEAR"
RAW_TOKEN_VALUE = "tok_live_raw_material_should_never_be_logged_0123456789"
BASE64_TOKEN_VALUE = base64.b64encode(RAW_TOKEN_VALUE.encode("utf-8")).decode("ascii")
AUTH_HEADER = f"Bearer {RAW_TOKEN_VALUE}"


def _fresh_conn():
    tmp = tempfile.TemporaryDirectory()
    db = Path(tmp.name) / "gategraph_token_exposure.db"
    init_db(db)
    conn = get_connection(db)
    seed_rules(conn)
    return tmp, conn


def _ensure_task(conn, task_id: str) -> None:
    conn.execute(
        """
        INSERT OR IGNORE INTO tasks
          (task_id, task_type, capabilities, input_source, data_sensitivity, secrets_involved, created_at)
        VALUES (?, 'token_exposure_probe', '[]', 'local', 'internal', 0, datetime('now'))
        """,
        (task_id,),
    )


def _event_blob(conn) -> str:
    rows = conn.execute(
        "SELECT event_id, type, input_json, evaluation_json, decision_json FROM events ORDER BY timestamp, event_id"
    ).fetchall()
    return json.dumps([dict(row) for row in rows], sort_keys=True, default=str)


def _assert_absent(blob: str, *values: str) -> None:
    leaked = [value for value in values if value and value in blob]
    assert not leaked, f"sensitive material leaked: {leaked[:3]}"


def audit_never_contains_raw_token() -> dict:
    tmp, conn = _fresh_conn()
    try:
        _ensure_task(conn, "TOK-EXPOSURE-RAW")
        event_logger.log_event(
            conn,
            event_id="EVT-EXPOSURE-RAW",
            idempotency_key="exposure:raw",
            correlation_id="CORR-EXPOSURE-RAW",
            causation_id=None,
            event_type="token_exposure_probe",
            task_id="TOK-EXPOSURE-RAW",
            actor_component="token_exposure_evidence",
            input_data={"raw_token": RAW_TOKEN_VALUE},
            evaluation={"token_value": RAW_TOKEN_VALUE},
            decision={"token_id": "TOK-SAFE-RAW", "token_hash": "sha256:SAFEHASHONLY"},
        )
        blob = _event_blob(conn)
        _assert_absent(blob, RAW_TOKEN_VALUE)
        assert "TOK-SAFE-RAW" in blob and "sha256:SAFEHASHONLY" in blob
        return {"raw_token_present": RAW_TOKEN_VALUE in blob, "safe_reference_present": True}
    finally:
        conn.close(); tmp.cleanup()


def base64_token_not_logged() -> dict:
    tmp, conn = _fresh_conn()
    try:
        _ensure_task(conn, "TOK-EXPOSURE-B64")
        event_logger.log_event(
            conn,
            event_id="EVT-EXPOSURE-B64",
            idempotency_key="exposure:b64",
            correlation_id="CORR-EXPOSURE-B64",
            causation_id=None,
            event_type="token_exposure_probe",
            task_id="TOK-EXPOSURE-B64",
            actor_component="token_exposure_evidence",
            input_data={"access_token": BASE64_TOKEN_VALUE},
            evaluation={"id_token": BASE64_TOKEN_VALUE},
            decision={"status": "blocked"},
        )
        blob = _event_blob(conn)
        _assert_absent(blob, BASE64_TOKEN_VALUE, RAW_TOKEN_VALUE)
        return {"base64_token_present": BASE64_TOKEN_VALUE in blob}
    finally:
        conn.close(); tmp.cleanup()


def authorization_header_redacted() -> dict:
    redacted = redact_authorization_header(AUTH_HEADER)
    blob = json.dumps(redacted, sort_keys=True)
    _assert_absent(blob, RAW_TOKEN_VALUE, AUTH_HEADER)
    assert redacted["redacted"] == "Bearer [REDACTED]"
    return {"redacted": redacted["redacted"], "header_hash": redacted["header_hash"]}


def explain_layer_no_secret_exposure() -> dict:
    tmp, conn = _fresh_conn()
    old_env = os.environ.get("GATEGRAPH_SECRET_PROVIDER_JSON")
    os.environ["GATEGRAPH_SECRET_PROVIDER_JSON"] = json.dumps({"V0115_API_KEY": SECRET_VALUE})
    calls: list[dict] = []
    try:
        task_id = "TOK-EXPOSURE-SECRET"
        session_budget_guard.create_session_budget(conn, session_id="SESSION-EXPOSURE-SECRET", max_session_cost_units=100, max_session_tasks=20, max_agent_cost_units=100)
        runtime_guard.create_budget(conn, task_id=task_id, max_steps=10, max_cost_units=100, repeated_action_limit=10)
        register_api_endpoint_policy(conn, policy_id="HTTP-V0115", allowed_host="api.example.test", allowed_path_prefixes=["/v1/"], allowed_methods=["GET"])
        secret_provider.register_env_secret_ref(conn, secret_ref_id="SEC-EXPOSURE-V0115", secret_name="V0115_API_KEY", allowed_endpoint_prefixes=["https://api.example.test/v1/"], allowed_capabilities=["api_call"])
        _ensure_task(conn, task_id)
        event = event_logger.log_event(
            conn,
            event_id="EVT-EXPOSURE-TOKEN-FIXTURE",
            idempotency_key="exposure:token-fixture",
            correlation_id="CORR-EXPOSURE-TOKEN-FIXTURE",
            causation_id=None,
            event_type="test_token_fixture",
            task_id=task_id,
            actor_component="token_exposure_evidence",
            input_data={"requested_capability": "api_call"},
            evaluation={"fixture": True},
            decision={"status": "allow", "final_capabilities": {"api_call": True}},
        )
        decision_id = "DEC-EXPOSURE-TOKEN-FIXTURE"
        conn.execute(
            """
            INSERT OR IGNORE INTO decisions
              (decision_id, task_id, event_id, status, final_caps_json, reason, matched_rules_json, created_at)
            VALUES (?, ?, ?, 'allow', '{"api_call": true}', 'test fixture api token', '[]', datetime('now'))
            """,
            (decision_id, task_id, event.event_id),
        )
        token = capability_token.issue_token(conn, decision_id, task_id, {"api_call": True})
        request = ExternalAPIRequest(
            request_id="REQ-EXPOSURE-SECRET",
            session_id="SESSION-EXPOSURE-SECRET",
            task_id=task_id,
            actor_id="agent-exposure",
            endpoint="https://api.example.test/v1/search",
            method="GET",
            secret_ref_id="SEC-EXPOSURE-V0115",
        )
        def transport(req, headers):
            calls.append(dict(headers))
            return ControlledAPIResponse(200, "ok", None)
        api_result = call_controlled_external_api(conn, request=request, token=token, transport=transport)
        assert api_result.decision == "completed"
        trace = build_task_trace(conn, task_id)
        trace_blob = json.dumps(trace, sort_keys=True, default=str)
        assert calls and calls[0].get("Authorization") == f"Bearer {SECRET_VALUE}"
        assert not contains_secret_value(trace, SECRET_VALUE)
        _assert_absent(trace_blob, SECRET_VALUE, f"Bearer {SECRET_VALUE}")
        return {"decision": api_result.decision, "secret_in_trace": SECRET_VALUE in trace_blob, "transport_calls": len(calls)}
    finally:
        if old_env is None:
            os.environ.pop("GATEGRAPH_SECRET_PROVIDER_JSON", None)
        else:
            os.environ["GATEGRAPH_SECRET_PROVIDER_JSON"] = old_env
        conn.close(); tmp.cleanup()


def unexpected_token_format_fails_closed() -> dict:
    blocked = []
    for value in ["", "   ", None]:
        try:
            redact_token_value(value)  # type: ignore[arg-type]
        except RedactionError:
            blocked.append(True)
        else:
            blocked.append(False)
    try:
        redact_authorization_header("Bearer")
    except RedactionError:
        auth_blocked = True
    else:
        auth_blocked = False
    assert all(blocked) and auth_blocked
    return {"token_formats_blocked": len(blocked), "bad_auth_header_blocked": auth_blocked}


def monitoring_export_no_sensitive_fields() -> dict:
    export = build_monitoring_export(
        budget_snapshot={"scope_id": "actor:x", "token_value": RAW_TOKEN_VALUE},
        incidents=[{"incident_id": "INC-X", "secret_value": SECRET_VALUE, "state": "open"}],
        alerts=[{"alert_id": "ALERT-X", "Authorization": AUTH_HEADER, "severity": "high"}],
        aggregated_alerts=[{"reason_code": "R", "signature": RAW_TOKEN_VALUE}],
        observability={"stop_reason_distribution": {}, "access_token": BASE64_TOKEN_VALUE},
    )
    blob = json.dumps(export, sort_keys=True, default=str)
    _assert_absent(blob, RAW_TOKEN_VALUE, BASE64_TOKEN_VALUE, SECRET_VALUE, AUTH_HEADER)
    assert blob.count("[REDACTED]") >= 4
    return {"sensitive_material_present": False, "redaction_count": blob.count("[REDACTED]")}


def main() -> int:
    tests = [
        ("audit_never_contains_raw_token", audit_never_contains_raw_token),
        ("base64_token_not_logged", base64_token_not_logged),
        ("authorization_header_redacted", authorization_header_redacted),
        ("explain_layer_no_secret_exposure", explain_layer_no_secret_exposure),
        ("unexpected_token_format_fails_closed", unexpected_token_format_fails_closed),
        ("monitoring_export_no_sensitive_fields", monitoring_export_no_sensitive_fields),
    ]
    failed: list[str] = []
    print("TOKEN EXPOSURE EVIDENCE")
    for name, fn in tests:
        try:
            print("✓", name, fn())
        except Exception as exc:
            failed.append(name)
            print("✗", name, repr(exc))
    print(f"Summary: {{'passed': {len(tests)-len(failed)}, 'failed': {len(failed)}}}")
    if failed:
        return 1
    print("PASS token_exposure_evidence")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
