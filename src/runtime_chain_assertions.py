"""
WHY: Runtime chain assertions make guard order an executable invariant, not just documentation.
INV: Enforcement is first; action_ready is reachable only after every required guard stage ran in order.
SEC: Skipped stages and invalid enforcement chains fail closed before an action can be treated as ready.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Final, Iterable, Tuple

RUNTIME_CHAIN_ORDER: Final[tuple[str, ...]] = (
    "enforcement",
    "flood_guard",
    "session_budget",
    "runtime_guard",
    "action_ready",
)


@dataclass(frozen=True)
class RuntimeChainAssertion:
    evaluated_stages: tuple[str, ...]
    terminal_stage: str
    enforcement_allowed: bool
    action_ready: bool

    def as_dict(self) -> dict[str, object]:
        return {
            "evaluated_stages": list(self.evaluated_stages),
            "terminal_stage": self.terminal_stage,
            "enforcement_allowed": self.enforcement_allowed,
            "action_ready": self.action_ready,
        }


def _normalize_stages(stages: Iterable[str]) -> tuple[str, ...]:
    return tuple(str(stage) for stage in stages)


def assert_runtime_chain(
    *,
    evaluated_stages: Iterable[str],
    terminal_stage: str,
    enforcement_allowed: bool,
) -> RuntimeChainAssertion:
    """Validate that a guard decision represents an ordered, non-skipped runtime chain.

    This function intentionally does not call guards itself. It validates the chain a caller
    claims to have evaluated, so tests can prove skipped-stage and invalid-chain cases fail
    closed without creating new runtime behavior.
    """
    stages = _normalize_stages(evaluated_stages)
    if not stages:
        raise PermissionError("runtime chain must include enforcement as first stage")
    if stages[0] != "enforcement":
        raise PermissionError("runtime chain must start with enforcement")
    if terminal_stage not in RUNTIME_CHAIN_ORDER:
        raise PermissionError(f"unknown terminal runtime stage: {terminal_stage}")
    unknown = [stage for stage in stages if stage not in RUNTIME_CHAIN_ORDER]
    if unknown:
        raise PermissionError(f"unknown runtime stage(s): {unknown}")
    if len(set(stages)) != len(stages):
        raise PermissionError("runtime chain contains duplicate stage evaluation")
    if stages[-1] != terminal_stage:
        raise PermissionError("runtime terminal_stage must match the last evaluated stage")

    expected_prefix = RUNTIME_CHAIN_ORDER[: RUNTIME_CHAIN_ORDER.index(terminal_stage) + 1]
    if stages != expected_prefix:
        raise PermissionError(
            "runtime chain order violation or skipped stage: "
            f"expected {expected_prefix}, got {stages}"
        )

    if not enforcement_allowed and terminal_stage != "enforcement":
        raise PermissionError("invalid enforcement chain: later guards may not run after enforcement denied")
    if terminal_stage != "enforcement" and not enforcement_allowed:
        raise PermissionError("invalid enforcement chain: enforcement must allow before downstream guards")

    action_ready = terminal_stage == "action_ready"
    if action_ready and stages != RUNTIME_CHAIN_ORDER:
        raise PermissionError("action_ready requires complete guard chain")

    return RuntimeChainAssertion(
        evaluated_stages=stages,
        terminal_stage=terminal_stage,
        enforcement_allowed=enforcement_allowed,
        action_ready=action_ready,
    )
