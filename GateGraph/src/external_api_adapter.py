"""
WHY: External API calls are side effects and must pass Enforcement plus GateGraph's guard pipeline first.
INV: all outbound integrations share the same Enforcement -> Session Budget -> Runtime Guard -> Action path.
SEC: callers cannot spoof enforcement_allowed; secrets are resolved only after all gates pass and are never logged.
"""

from __future__ import annotations

import sqlite3
import uuid
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Callable, Mapping, Optional

from src import event_logger
from src.capability_token import CapabilityToken
from src.enforcement import enforce
from src.guard_orchestrator import GuardPipelineDecision, evaluate_guard_pipeline
from src.http_policy import HTTPPolicyDecision, evaluate_http_policy
from src.secret_provider import SecretResolution, resolve_secret_for_api


@dataclass(frozen=True)
class ExternalAPIRequest:
    request_id: str
    session_id: str
    task_id: str
    actor_id: str
    endpoint: str
    method: str = "GET"
    payload_summary: str = ""
    projected_cost_units: int = 1
    timeout_ms: int = 1000
    mock_behavior: str = "success"  # success | timeout | rate_limit | server_error | untrusted_response
    requested_capability: str = "api_call"
    secret_ref_id: Optional[str] = None


@dataclass(frozen=True)
class ExternalAPIResult:
    request_id: str
    task_id: str
    decision: str  # completed | blocked | failed
    stage: str
    reason: str
    status_code: Optional[int]
    response_summary: str
    normalized_reason: Optional[dict]
    audit_event_id: str


@dataclass(frozen=True)
class ControlledAPIResponse:
    status_code: Optional[int]
    response_summary: str
    failure_reason: Optional[str] = None


# Test/integration seam: production code may supply a real transport, evidence tests supply a fake one.
APITransport = Callable[[ExternalAPIRequest, Mapping[str, str]], ControlledAPIResponse]


def call_mock_external_api(
    conn: sqlite3.Connection,
    *,
    request: ExternalAPIRequest,
    token: Optional[CapabilityToken],
) -> ExternalAPIResult:
    """Compatibility wrapper for deterministic mock calls; no network is touched."""
    return call_controlled_external_api(conn, request=request, token=token, transport=_mock_transport)


def call_controlled_external_api(
    conn: sqlite3.Connection,
    *,
    request: ExternalAPIRequest,
    token: Optional[CapabilityToken],
    transport: APITransport,
) -> ExternalAPIResult:
    """
    INV: external side effects execute only after Enforcement and Guard Orchestrator reach action_ready.
    SEC: secret material is resolved after authorization/budget/runtime gates and passed only to transport headers.
    """
    _ensure_task_exists(conn, request.task_id, secrets_involved=bool(request.secret_ref_id))
    enforcement = enforce(
        conn,
        token,
        requested_capability=request.requested_capability,
        task_id=request.task_id,
        correlation_id=request.request_id,
    )

    pipeline = evaluate_guard_pipeline(
        conn,
        enforcement_allowed=enforcement.allowed,
        enforcement_reason=enforcement.reason,
        session_id=request.session_id,
        task_id=request.task_id,
        actor_id=request.actor_id,
        action_type="external_api_call",
        target=f"{request.method}:{request.endpoint}",
        projected_cost_units=request.projected_cost_units,
    )

    if pipeline.decision != "continue":
        return _audit_result(
            conn,
            request=request,
            pipeline=pipeline,
            decision="blocked",
            status_code=None,
            response_summary="external call blocked before execution",
        )

    http_policy = evaluate_http_policy(conn, endpoint=request.endpoint, method=request.method)
    if not http_policy.allowed:
        return _audit_result(
            conn,
            request=request,
            pipeline=pipeline,
            decision="blocked",
            status_code=None,
            response_summary=http_policy.reason,
            http_policy=http_policy,
        )

    secret = resolve_secret_for_api(
        conn,
        secret_ref_id=request.secret_ref_id,
        endpoint=request.endpoint,
        requested_capability=request.requested_capability,
    )
    if not secret.allowed:
        return _audit_result(
            conn,
            request=request,
            pipeline=pipeline,
            decision="blocked",
            status_code=None,
            response_summary=secret.reason,
            secret_resolution=secret,
            http_policy=http_policy,
        )

    headers = _build_auth_headers(secret)
    response = transport(request, headers)
    if response.failure_reason:
        # WHY: external API failure is an execution failure, not an authorization failure.
        return _audit_result(
            conn,
            request=request,
            pipeline=pipeline,
            decision="failed",
            status_code=response.status_code,
            response_summary=response.failure_reason,
            secret_resolution=secret,
            http_policy=http_policy,
        )

    return _audit_result(
        conn,
        request=request,
        pipeline=pipeline,
        decision="completed",
        status_code=response.status_code,
        response_summary=response.response_summary,
        secret_resolution=secret,
        http_policy=http_policy,
    )


def _mock_transport(request: ExternalAPIRequest, headers: Mapping[str, str]) -> ControlledAPIResponse:
    status_code, response_summary, failed_reason = _mock_response(request.mock_behavior)
    return ControlledAPIResponse(status_code, response_summary, failed_reason)


def _build_auth_headers(secret: SecretResolution) -> Mapping[str, str]:
    if not secret.secret_value:
        return {}
    # SEC: only the transport sees this value; audit records mention the secret_ref_id, never the secret.
    return {"Authorization": f"Bearer {secret.secret_value}"}


def _mock_response(mock_behavior: str) -> tuple[Optional[int], str, Optional[str]]:
    behavior = (mock_behavior or "success").strip().lower()
    if behavior == "success":
        return 200, "mock external API success", None
    if behavior == "timeout":
        return None, "", "mock external API timeout"
    if behavior == "rate_limit":
        return 429, "", "mock external API rate limit"
    if behavior == "server_error":
        return 500, "", "mock external API server error"
    if behavior == "untrusted_response":
        return 200, "mock untrusted response captured as data, not instructions", None
    return None, "", f"unknown mock behavior: {mock_behavior}"


def _audit_result(
    conn: sqlite3.Connection,
    *,
    request: ExternalAPIRequest,
    pipeline: GuardPipelineDecision,
    decision: str,
    status_code: Optional[int],
    response_summary: str,
    secret_resolution: Optional[SecretResolution] = None,
    http_policy: Optional[HTTPPolicyDecision] = None,
) -> ExternalAPIResult:
    event_id = f"EVT-API-{uuid.uuid4().hex[:12].upper()}"
    secret_meta = _secret_audit_meta(request, secret_resolution)
    http_policy_meta = _http_policy_audit_meta(http_policy)
    with conn:
        event_logger.log_event(
            conn,
            event_id=event_id,
            idempotency_key=f"external-api:{request.request_id}",
            correlation_id=request.request_id,
            causation_id=pipeline.session_decision_id,
            event_type="external_api_call",
            task_id=request.task_id,
            actor_component="external_api_adapter",
            input_data={
                "request_id": request.request_id,
                "endpoint": request.endpoint,
                "method": request.method,
                "payload_summary": request.payload_summary,
                "projected_cost_units": request.projected_cost_units,
                "timeout_ms": request.timeout_ms,
                "mock_behavior": request.mock_behavior,
                "requested_capability": request.requested_capability,
                "secret_ref_id": request.secret_ref_id,
            },
            evaluation={
                "pipeline_stage": pipeline.stage,
                "pipeline_decision": pipeline.decision,
                "pipeline_reason": pipeline.reason,
                "normalized_reason": pipeline.normalized_reason,
                "http_policy": http_policy_meta,
                "secret_resolution": secret_meta,
            },
            decision={
                "status": decision,
                "status_code": status_code,
                "response_summary": response_summary,
            },
        )

    return ExternalAPIResult(
        request_id=request.request_id,
        task_id=request.task_id,
        decision=decision,
        stage=_result_stage(decision, pipeline, http_policy, secret_resolution),
        reason=response_summary if decision == "blocked" and pipeline.decision == "continue" else pipeline.reason,
        status_code=status_code,
        response_summary=response_summary,
        normalized_reason=pipeline.normalized_reason,
        audit_event_id=event_id,
    )


def _result_stage(decision: str, pipeline: GuardPipelineDecision, http_policy: Optional[HTTPPolicyDecision], secret_resolution: Optional[SecretResolution]) -> str:
    if decision != "blocked" or pipeline.decision != "continue":
        return pipeline.stage
    if http_policy is not None and not http_policy.allowed:
        return "http_policy"
    if secret_resolution is not None and not secret_resolution.allowed:
        return "secret_provider"
    return pipeline.stage


def _http_policy_audit_meta(http_policy: Optional[HTTPPolicyDecision]) -> dict:
    if http_policy is None:
        return {"status": "not_evaluated"}
    return {"status": "allowed" if http_policy.allowed else "blocked", "reason": http_policy.reason, "policy_id": http_policy.policy_id}


def _secret_audit_meta(request: ExternalAPIRequest, secret_resolution: Optional[SecretResolution]) -> dict:
    if not request.secret_ref_id:
        return {"required": False, "status": "not_required"}
    if secret_resolution is None:
        return {"required": True, "secret_ref_id": request.secret_ref_id, "status": "not_resolved"}
    return {
        "required": True,
        "secret_ref_id": request.secret_ref_id,
        "status": "resolved" if secret_resolution.allowed else "blocked",
        "reason": secret_resolution.reason,
        "provider": secret_resolution.secret_ref.provider if secret_resolution.secret_ref else None,
        "secret_name": secret_resolution.secret_ref.secret_name if secret_resolution.secret_ref else None,
    }


def _ensure_task_exists(conn: sqlite3.Connection, task_id: str, *, secrets_involved: bool = False) -> None:
    conn.execute(
        """
        INSERT OR IGNORE INTO tasks
          (task_id, task_type, capabilities, input_source, data_sensitivity, secrets_involved, created_at)
        VALUES (?, 'external_api_call', '["api_call"]', 'local', 'internal', ?, ?)
        """,
        (task_id, 1 if secrets_involved else 0, datetime.now(timezone.utc).isoformat()),
    )
