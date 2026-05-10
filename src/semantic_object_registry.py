"""
WHY: Semantic object rules need one deterministic read-only registry before release surfaces can be checked.
INV: Registry entries are descriptive only; they never grant runtime access, policy mutation, execution, or authority.
"""
from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

PROJECT_ROOT = Path(__file__).resolve().parents[1]
REGISTRY_PATH = PROJECT_ROOT / "registry" / "semantic_object_types.json"
FORBIDDEN_TRUE_FLAGS = (
    "authoritative",
    "executable",
    "runtime_access",
    "policy_mutation",
    "governance_influence",
    "semantic_promotion_allowed",
)
FORBIDDEN_TARGETS = {
    "execution",
    "runtime",
    "runtime_authority",
    "policy_mutation",
    "capability_creation",
    "governance_influence",
    "semantic_promotion",
}
CANONICAL_OBJECT_TYPES = (
    "replay_object",
    "explain_object",
    "monitoring_object",
    "proposal_object",
    "archive_object",
    "recovery_snapshot",
    "context_reference",
)


@dataclass(frozen=True)
class SemanticClassification:
    decision: str
    reason: str
    object_type: str | None = None
    surfaces: tuple[str, ...] = ()


def load_semantic_registry(path: Path | None = None) -> dict[str, Any]:
    registry_path = path or REGISTRY_PATH
    return json.loads(registry_path.read_text(encoding="utf-8"))


def get_object_spec(object_type: str, *, registry: dict[str, Any] | None = None) -> dict[str, Any]:
    data = registry or load_semantic_registry()
    return dict(data.get("object_types", {}).get(object_type, {}))


def classify_semantic_object(payload: dict[str, Any], *, registry: dict[str, Any] | None = None) -> SemanticClassification:
    object_type = payload.get("object_type")
    if not object_type:
        return SemanticClassification("stop", "SEM_OBJECT_TYPE_REQUIRED")
    spec = get_object_spec(str(object_type), registry=registry)
    if not spec:
        return SemanticClassification("stop", "SEM_UNKNOWN_OBJECT_TYPE", str(object_type))
    if any(bool(spec.get(flag)) for flag in FORBIDDEN_TRUE_FLAGS):
        return SemanticClassification("stop", "SEM_REGISTRY_AUTHORITY_FLAG_FORBIDDEN", str(object_type))
    return SemanticClassification("continue", "SEM_OBJECT_DESCRIPTIVE_ONLY", str(object_type), tuple(spec.get("surfaces", ())))


def assert_no_semantic_promotion(payload: dict[str, Any], target: str, *, registry: dict[str, Any] | None = None) -> SemanticClassification:
    classification = classify_semantic_object(payload, registry=registry)
    if classification.decision == "stop":
        return classification
    if target in FORBIDDEN_TARGETS:
        return SemanticClassification("stop", "SEMANTIC_PROMOTION_BLOCKED", classification.object_type, classification.surfaces)
    return SemanticClassification("continue", "SEMANTIC_OBJECT_REMAINS_DESCRIPTIVE", classification.object_type, classification.surfaces)


def registry_consistency_report(*, registry: dict[str, Any] | None = None) -> dict[str, Any]:
    data = registry or load_semantic_registry()
    object_types = data.get("object_types", {})
    missing = [name for name in CANONICAL_OBJECT_TYPES if name not in object_types]
    extra = sorted(set(object_types) - set(CANONICAL_OBJECT_TYPES))
    authority_violations = []
    surface_violations = []
    for name, spec in object_types.items():
        for flag in FORBIDDEN_TRUE_FLAGS:
            if bool(spec.get(flag)):
                authority_violations.append({"object_type": name, "flag": flag})
        surfaces = spec.get("surfaces", [])
        if not isinstance(surfaces, list) or not surfaces or any(not isinstance(s, str) or not s for s in surfaces):
            surface_violations.append({"object_type": name, "surfaces": surfaces})
    return {
        "schema_version": data.get("schema_version"),
        "canonical_count": len(CANONICAL_OBJECT_TYPES),
        "registered_count": len(object_types),
        "missing": missing,
        "extra": extra,
        "authority_violations": authority_violations,
        "surface_violations": surface_violations,
        "ok": not missing and not extra and not authority_violations and not surface_violations,
    }
