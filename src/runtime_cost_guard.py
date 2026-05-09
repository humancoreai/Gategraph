"""
WHY: Runtime Cost Guard adds deterministic pre-flight kill conditions before work is recorded.
INV: this module never grants capability, never mutates budgets, and only returns stricter constraints.
SEC: projected overruns and obvious loop/cost acceleration signals fail closed before another step is spent.
"""
from __future__ import annotations

from dataclasses import dataclass

from src.runtime_governance import compute_runtime_state


@dataclass(frozen=True)
class RuntimeCostGuardDecision:
    decision: str  # continue | stop
    reason: str
    escalation_state: str
    max_cost_for_action: int
    remaining_steps: int
    remaining_cost_units: int


def evaluate_runtime_cost_guard(
    *,
    max_steps: int,
    prior_steps: int,
    max_cost_units: int,
    used_cost_units: int,
    repeated_action_limit: int,
    repeated_count: int,
    projected_cost_units: int,
    loop_signal: bool = False,
) -> RuntimeCostGuardDecision:
    """
    INV: projection is evaluated before the normal Runtime Guard records a step.
    SEC: invalid or over-budget projected work is stopped; no best-effort recovery is attempted.
    """
    if projected_cost_units <= 0:
        return _stop("invalid projected_cost_units: must be positive", "blocked", 0, 0, 0)

    if max_steps <= 0 or max_cost_units <= 0 or repeated_action_limit <= 0:
        return _stop("runtime_cost_guard invalid runtime budget", "blocked", 0, 0, 0)

    remaining_steps = max(max_steps - prior_steps, 0)
    remaining_cost = max(max_cost_units - used_cost_units, 0)

    if remaining_steps <= 0:
        return _stop(
            f"projected_steps_violation: {prior_steps + 1} > {max_steps}",
            "blocked",
            0,
            remaining_steps,
            remaining_cost,
        )

    projected_total = used_cost_units + projected_cost_units
    if projected_total > max_cost_units:
        return _stop(
            f"projected_cost_violation: {projected_total} > {max_cost_units}",
            "blocked",
            0,
            remaining_steps,
            remaining_cost,
        )

    if repeated_count >= repeated_action_limit:
        return _stop(
            f"loop_detected: repeated_action_limit reached {repeated_count} >= {repeated_action_limit}",
            "blocked",
            0,
            remaining_steps,
            remaining_cost,
        )

    governance_state = compute_runtime_state(
        max_steps=max_steps,
        prior_steps=prior_steps,
        max_cost_units=max_cost_units,
        used_cost_units=used_cost_units,
        repeated_action_limit=repeated_action_limit,
        repeated_count=repeated_count,
        loop_signal=loop_signal,
    )

    if governance_state.state == "blocked":
        return _stop(
            f"escalation_limit_reached: {governance_state.reason}",
            governance_state.state,
            governance_state.max_cost_for_action,
            governance_state.remaining_steps,
            governance_state.remaining_cost_units,
        )

    if projected_cost_units > governance_state.max_cost_for_action:
        return _stop(
            f"projected_cost_throttled: cost_units {projected_cost_units} > max_cost_for_action {governance_state.max_cost_for_action}",
            governance_state.state,
            governance_state.max_cost_for_action,
            governance_state.remaining_steps,
            governance_state.remaining_cost_units,
        )

    return RuntimeCostGuardDecision(
        decision="continue",
        reason="runtime cost projection passed",
        escalation_state=governance_state.state,
        max_cost_for_action=governance_state.max_cost_for_action,
        remaining_steps=governance_state.remaining_steps,
        remaining_cost_units=governance_state.remaining_cost_units,
    )


def _stop(reason: str, state: str, max_cost_for_action: int, remaining_steps: int, remaining_cost_units: int) -> RuntimeCostGuardDecision:
    return RuntimeCostGuardDecision(
        decision="stop",
        reason=reason,
        escalation_state=state,
        max_cost_for_action=max_cost_for_action,
        remaining_steps=remaining_steps,
        remaining_cost_units=remaining_cost_units,
    )
