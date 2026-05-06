"""
WHY: Audit evidence is useful only if a reviewer can reconstruct the decision path without reading raw DB rows.
INV: trace building is read-only; it never changes Governance, Enforcement, Guard, HTTP Policy, or Secret state.
SEC: explanations summarize secret refs and provider metadata, never secret values.
"""
from __future__ import annotations

import json
import sqlite3
from typing import Any, Dict, List, Optional


def _load_json(value: Any) -> Any:
    if value is None:
        return None
    if isinstance(value, (dict, list)):
        return value
    try:
        return json.loads(value)
    except Exception:
        return value


def _rows(conn: sqlite3.Connection, query: str, params: tuple = ()) -> List[Dict[str, Any]]:
    return [dict(row) for row in conn.execute(query, params).fetchall()]


def build_task_trace(conn: sqlite3.Connection, task_id: str) -> Dict[str, Any]:
    """
    Build a reviewer-facing trace for one task.

    The trace is intentionally derived from persisted evidence only. It does not re-run policy logic
    and therefore cannot accidentally produce a different decision than the recorded execution.
    """
    events = _rows(
        conn,
        """
        SELECT event_id, correlation_id, causation_id, type, timestamp, actor_layer,
               actor_component, input_json, evaluation_json, decision_json
        FROM events
        WHERE task_id = ?
        ORDER BY timestamp, event_id
        """,
        (task_id,),
    )
    parsed_events: List[Dict[str, Any]] = []
    for event in events:
        parsed_events.append({
            "event_id": event["event_id"],
            "correlation_id": event["correlation_id"],
            "causation_id": event["causation_id"],
            "type": event["type"],
            "timestamp": event["timestamp"],
            "actor_layer": event["actor_layer"],
            "actor_component": event["actor_component"],
            "input": _load_json(event["input_json"]),
            "evaluation": _load_json(event["evaluation_json"]),
            "decision": _load_json(event["decision_json"]),
        })

    session_decisions = _rows(
        conn,
        """
        SELECT decision_id, session_id, task_id, actor_id, projected_cost_units,
               decision, reason, created_at
        FROM session_budget_decisions
        WHERE task_id = ?
        ORDER BY created_at, decision_id
        """,
        (task_id,),
    )
    runtime_decisions = _rows(
        conn,
        """
        SELECT decision_id, task_id, step_id, decision, reason, created_at
        FROM runtime_decisions
        WHERE task_id = ?
        ORDER BY created_at, decision_id
        """,
        (task_id,),
    )
    runtime_steps = _rows(
        conn,
        """
        SELECT step_id, step_index, actor_id, action_type, action_signature, cost_units, timestamp
        FROM runtime_steps
        WHERE task_id = ?
        ORDER BY step_index, timestamp, step_id
        """,
        (task_id,),
    )
    governance_decisions = _rows(
        conn,
        """
        SELECT decision_id, event_id, status, final_caps_json, reason, matched_rules_json, created_at
        FROM decisions
        WHERE task_id = ?
        ORDER BY created_at, decision_id
        """,
        (task_id,),
    )
    for decision in governance_decisions:
        decision["final_caps"] = _load_json(decision.pop("final_caps_json", None))
        decision["matched_rules"] = _load_json(decision.pop("matched_rules_json", None))

    api_events = [event for event in parsed_events if event["type"] == "external_api_call"]
    final_api_event: Optional[Dict[str, Any]] = api_events[-1] if api_events else None
    final_status = None
    final_stage = None
    final_reason_code = None
    if final_api_event:
        evaluation = final_api_event.get("evaluation") or {}
        decision = final_api_event.get("decision") or {}
        final_status = decision.get("status")
        http_policy = evaluation.get("http_policy") or {}
        secret_resolution = evaluation.get("secret_resolution") or {}
        if http_policy.get("status") == "blocked":
            final_stage = "http_policy"
        elif secret_resolution.get("status") == "blocked":
            final_stage = "secret_provider"
        else:
            final_stage = evaluation.get("pipeline_stage")
        normalized = evaluation.get("normalized_reason") or {}
        final_reason_code = normalized.get("code")

    return {
        "task_id": task_id,
        "final_status": final_status,
        "final_stage": final_stage,
        "final_reason_code": final_reason_code,
        "summary": _summarize(final_status, final_stage, final_reason_code, final_api_event),
        "counts": {
            "events": len(parsed_events),
            "api_events": len(api_events),
            "session_budget_decisions": len(session_decisions),
            "runtime_decisions": len(runtime_decisions),
            "runtime_steps": len(runtime_steps),
            "governance_decisions": len(governance_decisions),
        },
        "events": parsed_events,
        "session_budget_decisions": session_decisions,
        "runtime_decisions": runtime_decisions,
        "runtime_steps": runtime_steps,
        "governance_decisions": governance_decisions,
        "audit_refs": {
            "event_ids": [event["event_id"] for event in parsed_events],
            "session_decision_ids": [d["decision_id"] for d in session_decisions],
            "runtime_decision_ids": [d["decision_id"] for d in runtime_decisions],
            "runtime_step_ids": [s["step_id"] for s in runtime_steps],
            "governance_decision_ids": [d["decision_id"] for d in governance_decisions],
        },
    }


def _summarize(status: Optional[str], stage: Optional[str], code: Optional[str], event: Optional[Dict[str, Any]]) -> str:
    if event is None:
        return "No external API audit event recorded for this task."
    if status == "completed":
        return f"Action completed after guard pipeline reached {stage}; normalized reason {code}."
    if status == "blocked":
        return f"Action blocked at {stage}; normalized pipeline reason {code}."
    if status == "failed":
        return f"Action reached transport but execution failed at {stage}; normalized pipeline reason {code}."
    return "Action trace has an unknown final status; inspect raw events."


def contains_secret_value(trace: Dict[str, Any], secret_value: str) -> bool:
    """SEC: utility for evidence tests to prove trace output does not expose secret material."""
    if not secret_value:
        return False
    return secret_value in json.dumps(trace, sort_keys=True, ensure_ascii=False)
