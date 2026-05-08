"""
WHY: Runtime Governance computes deterministic escalation states from existing runtime budget facts.
INV: this module never grants capability; it only returns stricter constraints for downstream guards.
SEC: invalid or missing budget inputs resolve to blocked/fail-closed constraints.
"""

from __future__ import annotations

from dataclasses import dataclass

ESCALATION_ORDER = ("normal", "degraded", "throttled", "blocked")


@dataclass(frozen=True)
class RuntimeGovernanceState:
    state: str  # normal | degraded | throttled | blocked
    reason: str
    max_cost_for_action: int
    remaining_steps: int
    remaining_cost_units: int


def compute_runtime_state(
    *,
    max_steps: int,
    prior_steps: int,
    max_cost_units: int,
    used_cost_units: int,
    repeated_action_limit: int,
    repeated_count: int,
    loop_signal: bool = False,
) -> RuntimeGovernanceState:
    """
    INV: state transitions are deterministic thresholds; no model/heuristic may decide here.
    SEC: the returned max_cost_for_action can only reduce action size, never expand budget.
    """
    if max_steps <= 0 or max_cost_units <= 0 or repeated_action_limit <= 0:
        return RuntimeGovernanceState("blocked", "invalid runtime budget", 0, 0, 0)

    remaining_steps = max(max_steps - prior_steps, 0)
    remaining_cost = max(max_cost_units - used_cost_units, 0)
    if remaining_steps <= 0 or remaining_cost <= 0:
        return RuntimeGovernanceState("blocked", "runtime budget exhausted", 0, remaining_steps, remaining_cost)

    cost_ratio = used_cost_units / max_cost_units
    step_ratio = prior_steps / max_steps
    repeat_ratio = repeated_count / repeated_action_limit

    state = "normal"
    reasons: list[str] = []

    if cost_ratio >= 0.90 or step_ratio >= 0.90 or repeat_ratio >= 0.90:
        state = "throttled"
        reasons.append("runtime budget above 90% threshold")
    elif cost_ratio >= 0.70 or step_ratio >= 0.70 or repeat_ratio >= 0.70:
        state = "degraded"
        reasons.append("runtime budget above 70% threshold")

    if loop_signal:
        state = escalate_state(state)
        reasons.append("loop signal escalated state")

    # SEC: throttling means only one minimal-cost action can pass; blocked means no action passes.
    if state == "blocked":
        max_cost_for_action = 0
    elif state == "throttled":
        max_cost_for_action = min(1, remaining_cost)
    elif state == "degraded":
        max_cost_for_action = max(1, remaining_cost // 2)
    else:
        max_cost_for_action = remaining_cost

    return RuntimeGovernanceState(
        state=state,
        reason="; ".join(reasons) if reasons else "within runtime governance thresholds",
        max_cost_for_action=max_cost_for_action,
        remaining_steps=remaining_steps,
        remaining_cost_units=remaining_cost,
    )


def escalate_state(state: str) -> str:
    try:
        idx = ESCALATION_ORDER.index(state)
    except ValueError:
        return "blocked"
    return ESCALATION_ORDER[min(idx + 1, len(ESCALATION_ORDER) - 1)]
