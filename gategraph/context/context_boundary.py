"""
WHY: Instruction-looking text must not become authority by phrasing alone.
INV: Boundary output is a data representation; it never produces capabilities or policy mutation.
SEC: Suspicious context indicators are visible for audit/explain only and are not autonomous blockers.
"""
from __future__ import annotations
import re
from dataclasses import dataclass
from typing import Any, Mapping
from .context_classifier import ContextClassification, classify_context
SUSPICIOUS_PATTERNS = (
    ("hidden_instruction_markers", re.compile(r"(?i)(ignore previous|disregard prior|system prompt|developer message)")),
    ("fake_operator_claims", re.compile(r"(?i)(operator approved|admin override|authorized by operator|human approved)")),
    ("recursive_delegation_phrases", re.compile(r"(?i)(delegate this to|spawn another agent|create a subagent|ask another agent)")),
    ("embedded_authority_patterns", re.compile(r"(?i)(you now have permission|grant capability|change policy|override governance)")),
)
@dataclass(frozen=True)
class BoundaryResult:
    decision: str; reason: str; data: str | None = None; executable: bool = False; governance_influence: bool = False; authority_granted: bool = False; capability_created: bool = False; policy_mutation: bool = False; markers: tuple[str, ...] = (); classification: ContextClassification | None = None
    def to_dict(self) -> dict[str, Any]:
        out = {"decision":self.decision,"reason":self.reason,"data":self.data,"executable":self.executable,"governance_influence":self.governance_influence,"authority_granted":self.authority_granted,"capability_created":self.capability_created,"policy_mutation":self.policy_mutation,"markers":list(self.markers)}
        if self.classification is not None: out["classification"] = self.classification.to_dict()
        return out
def suspicious_context_markers(text: str) -> tuple[str, ...]:
    return tuple(name for name, pattern in SUSPICIOUS_PATTERNS if pattern.search(text))
def enforce_instruction_data_boundary(payload: Mapping[str, Any], content: str) -> BoundaryResult:
    classification = classify_context(payload)
    if not classification.allowed or classification.provenance is None: return BoundaryResult("stop", classification.reason, classification=classification)
    provenance = classification.provenance
    if provenance.executable: return BoundaryResult("stop", "CTX_EXECUTABLE_CONTEXT_FORBIDDEN", classification=classification)
    if provenance.context_type in {"untrusted_external_context", "replay_context", "proposal_context"} and provenance.governance_influence:
        return BoundaryResult("stop", "CTX_GOVERNANCE_INFLUENCE_FORBIDDEN", classification=classification)
    markers = tuple(dict.fromkeys((*classification.markers, *suspicious_context_markers(content))))
    return BoundaryResult("continue", "CTX_DATA_ONLY", str(content), False, provenance.governance_influence, False, False, False, markers, classification)
def mark_explain_replay_context(payload: Mapping[str, Any], content: str) -> BoundaryResult:
    result = enforce_instruction_data_boundary(payload, content)
    if result.decision != "continue": return result
    provenance = result.classification.provenance if result.classification else None
    if provenance is None or provenance.context_type not in {"replay_context", "proposal_context", "untrusted_external_context"}: return result
    markers = tuple(dict.fromkeys((*result.markers, "descriptive_only", "non_executable", "reference_context")))
    return BoundaryResult("continue", "CTX_REFERENCE_ONLY", result.data, False, False, False, False, False, markers, result.classification)
