"""
WHY: Observability reconstructs decisions from persisted runtime evidence without influencing execution.
INV: This module is read-only; it never records steps, updates budgets, or changes guard outcomes.
SEC: unknown/missing data is reported explicitly instead of being interpreted into a safer-looking answer.
"""
from __future__ import annotations

import sqlite3
from dataclasses import dataclass, asdict
from typing import Any

from src.reason_normalizer import normalize_as_dict

GUARD_SEQUENCE = ("enforcement", "flood_guard", "session_budget", "runtime_cost_guard", "runtime_guard")


def _runtime_guard_for_reason(reason: str) -> str:
    raw = (reason or "").strip().lower()
    if raw.startswith((
        "projected_cost_violation",
        "projected_steps_violation",
        "projected_cost_throttled",
        "loop_detected",
        "escalation_limit_reached",
        "invalid projected_cost_units",
        "runtime_cost_guard invalid runtime budget",
    )):
        return "runtime_cost_guard"
    return "runtime_guard"


def _normalization_stage(guard: str) -> str:
    # WHY: reason_normalizer keeps runtime-cost preflight reasons under the runtime_guard stage for API stability.
    return "runtime_guard" if guard == "runtime_cost_guard" else guard


def _copy_row(row: sqlite3.Row | None) -> dict[str, Any] | None:
    return dict(row) if row is not None else None


def reconstruct_decision_trace(conn: sqlite3.Connection, task_id: str) -> dict[str, Any]:
    """Build a complete runtime decision chain for one task from persisted evidence only."""
    budget = _copy_row(conn.execute(
        """
        SELECT budget_id, task_id, max_steps, max_runtime_seconds, max_cost_units,
               repeated_action_limit, created_at
        FROM runtime_budgets
        WHERE task_id = ?
        ORDER BY created_at DESC
        LIMIT 1
        """,
        (task_id,),
    ).fetchone())

    step_rows = [dict(r) for r in conn.execute(
        """
        SELECT step_id, task_id, step_index, actor_id, action_type,
               action_signature, cost_units, timestamp
        FROM runtime_steps
        WHERE task_id = ?
        ORDER BY step_index ASC, timestamp ASC
        """,
        (task_id,),
    ).fetchall()]
    steps_by_id = {row["step_id"]: row for row in step_rows}

    decision_rows = [dict(r) for r in conn.execute(
        """
        SELECT decision_id, task_id, step_id, decision, reason, created_at
        FROM runtime_decisions
        WHERE task_id = ?
        ORDER BY created_at ASC, decision_id ASC
        """,
        (task_id,),
    ).fetchall()]

    used_cost = 0
    trace_steps: list[dict[str, Any]] = []
    for index, decision in enumerate(decision_rows, start=1):
        step = steps_by_id.get(decision.get("step_id")) if decision.get("step_id") else None
        if step is not None:
            used_cost += int(step.get("cost_units") or 0)
        guard = _runtime_guard_for_reason(str(decision.get("reason") or ""))
        normalized = normalize_as_dict(_normalization_stage(guard), str(decision.get("reason") or ""))
        max_cost = int(budget.get("max_cost_units") or 0) if budget else 0
        budget_link = {
            "budget_id": budget.get("budget_id") if budget else None,
            "max_cost_units": max_cost,
            "used_cost_units": used_cost,
            "remaining_cost_units": max(max_cost - used_cost, 0) if budget else 0,
        }
        trace_steps.append({
            "index": index,
            "guard": guard,
            "stop_stage": guard if decision.get("decision") == "stop" else None,
            "decision": decision.get("decision"),
            "reason": decision.get("reason"),
            "normalized_reason": normalized,
            "runtime_step": step,
            "budget_link": budget_link,
            "created_at": decision.get("created_at"),
        })

    final = trace_steps[-1] if trace_steps else None
    return {
        "task_id": task_id,
        "guard_sequence": list(GUARD_SEQUENCE),
        "runtime_budget": budget,
        "runtime_steps": step_rows,
        "decision_trace": trace_steps,
        "final": {
            "decision": final.get("decision") if final else "unknown",
            "triggering_guard": final.get("guard") if final else None,
            "stop_stage": final.get("stop_stage") if final else None,
            "normalized_reason": final.get("normalized_reason") if final else None,
        },
    }


def build_explain_snapshot(conn: sqlite3.Connection, task_id: str) -> dict[str, Any]:
    """Compact read-only answer to: why did this task stop or continue?"""
    trace = reconstruct_decision_trace(conn, task_id)
    final = trace["final"]
    runtime_steps = trace["runtime_steps"]
    total_cost = sum(int(step.get("cost_units") or 0) for step in runtime_steps)
    max_cost = int((trace.get("runtime_budget") or {}).get("max_cost_units") or 0)
    return {
        "task_id": task_id,
        "final_decision": final["decision"],
        "triggering_guard": final["triggering_guard"],
        "normalized_reason": final["normalized_reason"],
        "metrics": {
            "cost": total_cost,
            "steps": len(runtime_steps),
            "budget_used": (total_cost / max_cost) if max_cost else 0,
        },
    }


def build_cost_timeline(conn: sqlite3.Connection, task_id: str) -> list[dict[str, Any]]:
    trace = reconstruct_decision_trace(conn, task_id)
    timeline: list[dict[str, Any]] = []
    running_cost = 0
    for item in trace["decision_trace"]:
        step = item.get("runtime_step")
        if step:
            running_cost += int(step.get("cost_units") or 0)
        timeline.append({
            "step": step.get("step_index") if step else None,
            "cost": running_cost,
            "decision": item.get("decision"),
            "guard": item.get("guard"),
        })
    return timeline


def build_observability_aggregation(conn: sqlite3.Connection) -> dict[str, Any]:
    """Aggregate runtime stop reasons and guard attribution from existing decisions."""
    rows = [dict(r) for r in conn.execute(
        "SELECT decision, reason FROM runtime_decisions ORDER BY created_at ASC"
    ).fetchall()]
    stop_reason_distribution: dict[str, int] = {}
    guard_distribution: dict[str, int] = {}
    loop_detection_count = 0
    for row in rows:
        guard = _runtime_guard_for_reason(str(row.get("reason") or ""))
        guard_distribution[guard] = guard_distribution.get(guard, 0) + 1
        if row.get("decision") == "stop":
            norm = normalize_as_dict(_normalization_stage(guard), str(row.get("reason") or ""))
            code = str(norm.get("code"))
            stop_reason_distribution[code] = stop_reason_distribution.get(code, 0) + 1
            if code in {"RT_LOOP_DETECTED", "RT_REPEATED_ACTION"}:
                loop_detection_count += 1
    return {
        "stop_reason_distribution": stop_reason_distribution,
        "guard_distribution": guard_distribution,
        "loop_detection_count": loop_detection_count,
    }
