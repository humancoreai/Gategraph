"""
WHY: API boundary classification prevents future integrations from treating every
module function as a valid public entry path.
INV: Public entry is service_adapter only; Governance remains internal and must
receive an explicit trusted entry context.
SEC: Forbidden paths fail closed before Governance can make a decision.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Final, Literal

BoundaryClass = Literal["public", "internal", "forbidden"]

PUBLIC_ENTRY_COMPONENT: Final[str] = "service_adapter"
INTERNAL_COMPONENTS: Final[set[str]] = {"governance", "runtime_guard", "session_budget_guard", "enforcement"}
TEST_ONLY_COMPONENT: Final[str] = "test_harness"
FORBIDDEN_DIRECT_COMPONENTS: Final[set[str]] = {"external_plugin", "framework_adapter", "agent_runtime", "operator_ui"}


@dataclass(frozen=True)
class BoundaryClassification:
    component: str
    boundary_class: BoundaryClass
    reason: str

    def as_dict(self) -> dict[str, str]:
        return {
            "component": self.component,
            "boundary_class": self.boundary_class,
            "reason": self.reason,
        }


def classify_component(component: str) -> BoundaryClassification:
    if component == PUBLIC_ENTRY_COMPONENT:
        return BoundaryClassification(component, "public", "only supported public evaluation entry")
    if component == TEST_ONLY_COMPONENT:
        return BoundaryClassification(component, "internal", "test-only direct governance compatibility path")
    if component in INTERNAL_COMPONENTS:
        return BoundaryClassification(component, "internal", "internal implementation component, not public entry")
    if component in FORBIDDEN_DIRECT_COMPONENTS:
        return BoundaryClassification(component, "forbidden", "external or agent-side component may not enter governance directly")
    return BoundaryClassification(component, "forbidden", "unknown component has no governance entry authority")


def assert_component_boundary(component: str, *, public_entry: bool, direct_governance_call: bool) -> BoundaryClassification:
    classification = classify_component(component)
    if classification.boundary_class == "forbidden":
        raise PermissionError(f"forbidden governance entry component: {component}")
    if public_entry and component != PUBLIC_ENTRY_COMPONENT:
        raise PermissionError("public governance entry must pass through service_adapter")
    if component == PUBLIC_ENTRY_COMPONENT and not public_entry:
        raise PermissionError("service_adapter entry must be marked as public_entry")
    if direct_governance_call and component != TEST_ONLY_COMPONENT:
        raise PermissionError("direct governance invocation is reserved for isolated evidence tests")
    return classification
