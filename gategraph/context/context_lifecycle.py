"""
WHY: Context lifecycle transitions must not become hidden authority promotion paths.
INV: Lifecycle handling is descriptive and fail-closed; it never mutates provenance, grants execution, or changes governance influence.
SEC: Replay/explain/proposal context cannot be rehydrated into trusted or runtime authority by transition labels.
"""
from __future__ import annotations
from dataclasses import asdict, dataclass
from typing import Any, Mapping
from .context_classifier import ContextClassification, classify_context
LIFECYCLE_STATES={"received","classified","bounded","referenced","archived","replayed","expired"}
ALLOWED_TRANSITIONS={("received","classified"),("classified","bounded"),("bounded","referenced"),("referenced","archived"),("archived","replayed"),("replayed","referenced"),("referenced","expired"),("archived","expired")}
REFERENCE_ONLY_CONTEXT_TYPES={"untrusted_external_context","replay_context","proposal_context"}
FORBIDDEN_REHYDRATION_TARGETS={"trusted_system_context","trusted_operator_context","transient_runtime_context"}
LIFECYCLE_MARKERS=("descriptive_only","non_executable","reference_context","lifecycle_observed")
@dataclass(frozen=True)
class ContextLifecycleResult:
    decision:str; reason:str; from_state:str|None=None; to_state:str|None=None; context_type:str|None=None; executable:bool=False; governance_influence:bool=False; provenance_mutated:bool=False; markers:tuple[str,...]=(); classification:ContextClassification|None=None
    @property
    def allowed(self)->bool: return self.decision=="continue"
    def to_dict(self)->dict[str,Any]:
        out=asdict(self)
        if self.classification is not None: out["classification"]=self.classification.to_dict()
        return out
def observe_context_lifecycle(payload:Mapping[str,Any], from_state:str, to_state:str, *, target_context_type:str|None=None)->ContextLifecycleResult:
    classification=classify_context(payload)
    if not classification.allowed or classification.provenance is None:
        return ContextLifecycleResult("stop",classification.reason,classification=classification)
    provenance=classification.provenance
    if from_state not in LIFECYCLE_STATES or to_state not in LIFECYCLE_STATES:
        return ContextLifecycleResult("stop","CTX_LIFECYCLE_UNKNOWN_STATE",from_state,to_state,provenance.context_type,classification=classification)
    if (from_state,to_state) not in ALLOWED_TRANSITIONS:
        return ContextLifecycleResult("stop","CTX_LIFECYCLE_TRANSITION_FORBIDDEN",from_state,to_state,provenance.context_type,classification=classification)
    if target_context_type is not None and target_context_type != provenance.context_type:
        if provenance.context_type in REFERENCE_ONLY_CONTEXT_TYPES or target_context_type in FORBIDDEN_REHYDRATION_TARGETS:
            return ContextLifecycleResult("stop","CTX_REHYDRATION_FORBIDDEN",from_state,to_state,provenance.context_type,classification=classification)
        return ContextLifecycleResult("stop","CTX_PROVENANCE_MUTATION_FORBIDDEN",from_state,to_state,provenance.context_type,classification=classification)
    markers=tuple(dict.fromkeys((*classification.markers,*LIFECYCLE_MARKERS)))
    return ContextLifecycleResult("continue","CTX_LIFECYCLE_OBSERVED",from_state,to_state,provenance.context_type,False,provenance.governance_influence,False,markers,classification)
