"""Deterministic runtime/reference object boundary helpers.

INV: Reference objects cannot become execution, policy, capability, or authority inputs.
"""
from __future__ import annotations
from dataclasses import dataclass

RUNTIME_OBJECT = "runtime_object"
REFERENCE_TYPES = {"reference_object", "replay_object", "explain_object", "archive_object", "monitoring_object", "proposal_object", "review_object"}
FORBIDDEN_PROMOTIONS = {"execution", "policy_mutation", "capability_creation", "runtime_authority", "governance_influence"}

@dataclass(frozen=True)
class ObjectBoundaryDecision:
    decision: str
    reason: str
    object_type: str | None
    target: str | None
    executable: bool = False
    governance_influence: bool = False

def classify_object(payload: dict) -> ObjectBoundaryDecision:
    object_type = payload.get("object_type")
    if not object_type:
        return ObjectBoundaryDecision("stop", "SEM_OBJECT_TYPE_REQUIRED", None, None)
    if object_type == RUNTIME_OBJECT:
        return ObjectBoundaryDecision("continue", "SEM_RUNTIME_OBJECT", object_type, None, executable=bool(payload.get("executable", False)), governance_influence=bool(payload.get("governance_influence", False)))
    if object_type in REFERENCE_TYPES:
        return ObjectBoundaryDecision("continue", "SEM_REFERENCE_OBJECT", object_type, None, executable=False, governance_influence=False)
    return ObjectBoundaryDecision("stop", "SEM_UNKNOWN_OBJECT_TYPE", object_type, None)

def assert_no_reference_promotion(payload: dict, target: str) -> ObjectBoundaryDecision:
    base = classify_object(payload)
    if base.decision == "stop":
        return base
    if base.object_type in REFERENCE_TYPES and target in FORBIDDEN_PROMOTIONS:
        return ObjectBoundaryDecision("stop", "SEM_REFERENCE_PROMOTION_BLOCKED", base.object_type, target)
    if base.object_type in REFERENCE_TYPES:
        return ObjectBoundaryDecision("continue", "SEM_REFERENCE_REMAINS_DESCRIPTIVE", base.object_type, target)
    return ObjectBoundaryDecision("continue", "SEM_RUNTIME_PATH_EXPLICIT", base.object_type, target, executable=base.executable, governance_influence=base.governance_influence)
