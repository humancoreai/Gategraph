"""
WHY: External API calls are side effects and must pass Enforcement plus GateGraph's guard pipeline first.
INV: this adapter never calls real networks; v0.8.5 uses deterministic mock responses only.
SEC: caller cannot spoof enforcement_allowed; adapter invokes Enforcement internally with the provided token.
SEC: no secrets are logged; request payloads are summarized, not persisted verbatim.
"""

from __future__ import annotations

import sqlite3
import uuid
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Optional

from src import event_logger
from src.capability_token import CapabilityToken
from src.enforcement import enforce
from src.guard_orchestrator import GuardPipelineDecision, evaluate_guard_pipeline


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


def call_mock_external_api(
    conn: sqlite3.Connection,
    *,
    request: ExternalAPIRequest,
    token: Optional[CapabilityToken],
) -> ExternalAPIResult:
    """
    INV: external side effect is simulated only after Enforcement and Guard Orchestrator reach action_ready.
    SEC: Enforcement is called inside this adapter, so callers cannot bypass it with a forged boolean.
    """
    _ensure_task_exists(conn, request.task_id)
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

    status_code, response_summary, failed_reason = _mock_response(request.mock_behavior)

    if failed_reason:
        # WHY: external API failure is an execution failure, not an authorization failure.
        return _audit_result(
            conn,
            request=request,
            pipeline=pipeline,
            decision="failed",
            status_code=status_code,
            response_summary=failed_reason,
        )

    return _audit_result(
        conn,
        request=request,
        pipeline=pipeline,
        decision="completed",
        status_code=status_code,
        response_summary=response_summary,
    )


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
) -> ExternalAPIResult:
    event_id = f"EVT-API-{uuid.uuid4().hex[:12].upper()}"
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
            },
            evaluation={
                "pipeline_stage": pipeline.stage,
                "pipeline_decision": pipeline.decision,
                "pipeline_reason": pipeline.reason,
                "normalized_reason": pipeline.normalized_reason,
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
        stage=pipeline.stage,
        reason=pipeline.reason,
        status_code=status_code,
        response_summary=response_summary,
        normalized_reason=pipeline.normalized_reason,
        audit_event_id=event_id,
    )


def _ensure_task_exists(conn: sqlite3.Connection, task_id: str) -> None:
    conn.execute(
        """
        INSERT OR IGNORE INTO tasks
          (task_id, task_type, capabilities, input_source, data_sensitivity, secrets_involved, created_at)
        VALUES (?, 'external_api_call', '["api_call"]', 'local', 'internal', 0, ?)
        """,
        (task_id, datetime.now(timezone.utc).isoformat()),
    )
