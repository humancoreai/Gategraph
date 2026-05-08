"""
WHY: Guard Orchestrator makes protection order deterministic and auditable.
INV: this layer never grants capabilities; it can only preserve an Enforcement allow or stop before action.
SEC: fail closed on missing/invalid prerequisites and stop at the earliest guard boundary.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

import sqlite3

from src import flood_guard, runtime_guard, session_budget_guard
from src.reason_normalizer import normalize_as_dict


@dataclass(frozen=True)
class GuardPipelineDecision:
    decision: str  # continue | stop
    stage: str     # enforcement | flood_guard | session_budget | runtime_guard | action_ready
    reason: str
    enforcement_allowed: bool
    session_decision_id: Optional[str] = None
    runtime_step_id: Optional[str] = None
    normalized_reason: Optional[dict] = None


def _decision(
    *,
    decision: str,
    stage: str,
    reason: str,
    enforcement_allowed: bool,
    session_decision_id: Optional[str] = None,
    runtime_step_id: Optional[str] = None,
) -> GuardPipelineDecision:
    return GuardPipelineDecision(
        decision=decision,
        stage=stage,
        reason=reason,
        enforcement_allowed=enforcement_allowed,
        session_decision_id=session_decision_id,
        runtime_step_id=runtime_step_id,
        normalized_reason=normalize_as_dict(stage, reason),
    )


def evaluate_guard_pipeline(
    conn: sqlite3.Connection,
    *,
    enforcement_allowed: bool,
    enforcement_reason: str,
    session_id: str,
    task_id: str,
    actor_id: str,
    action_type: str,
    target: str = "",
    projected_cost_units: int = 1,
    flood_config: flood_guard.FloodGuardConfig | None = None,
) -> GuardPipelineDecision:
    """
    Order:
    1. Enforcement result must already be allow.
    2. Flood Guard checks actor-scoped global window limits.
    3. Session Budget Guard checks aggregate limits.
    4. Runtime Guard checks per-task limits.
    5. Action may proceed only if all prior gates continue.

    INV: Flood Guard runs before session reservation to avoid reserving budget for a blocked flood attempt.
    INV: Session Guard is evaluated before Runtime Guard to avoid spending per-task runtime work after global exhaustion.
    """
    if not enforcement_allowed:
        return _decision(
            decision="stop",
            stage="enforcement",
            reason=enforcement_reason or "enforcement blocked",
            enforcement_allowed=False,
        )

    flood_decision = flood_guard.evaluate_flood_guard(
        conn,
        actor_id=actor_id,
        projected_cost_units=projected_cost_units,
        config=flood_config,
    )
    if flood_decision.decision != "continue":
        return _decision(
            decision="stop",
            stage="flood_guard",
            reason=flood_decision.reason,
            enforcement_allowed=True,
        )

    session_decision = session_budget_guard.evaluate_before_task(
        conn,
        session_id=session_id,
        task_id=task_id,
        actor_id=actor_id,
        projected_cost_units=projected_cost_units,
    )
    if session_decision.decision != "continue":
        return _decision(
            decision="stop",
            stage="session_budget",
            reason=session_decision.reason,
            enforcement_allowed=True,
            session_decision_id=session_decision.decision_id,
        )

    runtime_decision = runtime_guard.evaluate_before_step(
        conn,
        task_id=task_id,
        actor_id=actor_id,
        action_type=action_type,
        target=target,
        cost_units=projected_cost_units,
    )
    if runtime_decision.decision != "continue":
        return _decision(
            decision="stop",
            stage="runtime_guard",
            reason=runtime_decision.reason,
            enforcement_allowed=True,
            session_decision_id=session_decision.decision_id,
            runtime_step_id=runtime_decision.step_id,
        )

    return _decision(
        decision="continue",
        stage="action_ready",
        reason="all guards passed",
        enforcement_allowed=True,
        session_decision_id=session_decision.decision_id,
        runtime_step_id=runtime_decision.step_id,
    )
