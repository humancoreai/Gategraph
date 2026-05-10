"""
WHY: Context is a governance boundary, not an authority source.
INV: Unknown type, missing provenance or inconsistent trust metadata fails closed.
SEC: Untrusted/replay/proposal context is always non-executable and cannot influence governance.
"""
from __future__ import annotations
from dataclasses import asdict, dataclass
from typing import Any, Mapping
CONTEXT_TYPES = {
    "trusted_system_context": {"trust_level":"trusted","governance_influence":True,"executable":False,"replayable":False},
    "trusted_operator_context": {"trust_level":"trusted","governance_influence":False,"executable":False,"replayable":True},
    "untrusted_external_context": {"trust_level":"untrusted","governance_influence":False,"executable":False,"replayable":True},
    "transient_runtime_context": {"trust_level":"runtime","governance_influence":False,"executable":False,"replayable":False},
    "replay_context": {"trust_level":"reference","governance_influence":False,"executable":False,"replayable":True},
    "proposal_context": {"trust_level":"proposal","governance_influence":False,"executable":False,"replayable":True},
}
REQUIRED_FIELDS = {"context_type","source","trust_level","governance_influence","executable","replayable"}
DESCRIPTIVE_MARKERS = ("descriptive_only", "non_executable", "reference_context")
@dataclass(frozen=True)
class ContextProvenance:
    context_type: str; source: str; trust_level: str; governance_influence: bool; executable: bool; replayable: bool
    def to_dict(self) -> dict[str, Any]: return asdict(self)
@dataclass(frozen=True)
class ContextClassification:
    decision: str; reason: str; provenance: ContextProvenance | None = None; markers: tuple[str, ...] = ()
    @property
    def allowed(self) -> bool: return self.decision == "continue"
    def to_dict(self) -> dict[str, Any]:
        out = {"decision": self.decision, "reason": self.reason, "markers": list(self.markers)}
        if self.provenance is not None: out["provenance"] = self.provenance.to_dict()
        return out
def _fail(reason: str) -> ContextClassification: return ContextClassification("stop", reason)
def classify_context(payload: Mapping[str, Any]) -> ContextClassification:
    if missing := sorted(REQUIRED_FIELDS - set(payload.keys())): return _fail("CTX_PROVENANCE_REQUIRED")
    context_type = payload.get("context_type")
    if context_type not in CONTEXT_TYPES: return _fail("CTX_UNKNOWN_TYPE")
    source = payload.get("source")
    if not isinstance(source, str) or not source.strip(): return _fail("CTX_SOURCE_REQUIRED")
    expected = CONTEXT_TYPES[context_type]
    for key, expected_value in expected.items():
        if payload.get(key) != expected_value: return _fail("CTX_PROVENANCE_INCONSISTENT")
    provenance = ContextProvenance(str(context_type), source, str(payload["trust_level"]), bool(payload["governance_influence"]), bool(payload["executable"]), bool(payload["replayable"]))
    markers = DESCRIPTIVE_MARKERS if context_type in {"replay_context", "proposal_context", "untrusted_external_context"} else ()
    return ContextClassification("continue", "CTX_CLASSIFIED", provenance, markers)
def required_provenance(context_type: str, source: str) -> dict[str, Any]:
    if context_type not in CONTEXT_TYPES: raise ValueError("unknown context_type")
    if not isinstance(source, str) or not source.strip(): raise ValueError("source required")
    return {"context_type": context_type, "source": source, **CONTEXT_TYPES[context_type]}
