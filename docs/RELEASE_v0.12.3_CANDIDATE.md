# GateGraph v0.12.3_CANDIDATE

Base: v0.12.2_STABLE  
Status: candidate  
Phase: Semantic & Registry Consolidation

## Scope

v0.12.3_CANDIDATE consolidates descriptive semantic object rules, invariant/surface/evidence mapping, incident lifecycle semantics and evidence-surface coupling.

## Added evidence

- `semantic_registry_evidence.py`
- `invariant_surface_mapping_evidence.py`
- `incident_lifecycle_consistency_evidence.py`
- `semantic_drift_detection_evidence.py`
- `evidence_surface_consistency_evidence.py`

## Invariants

- Semantic registries are descriptive only.
- Reference-class objects are non-authoritative and non-executable.
- Semantic promotion into runtime, execution, policy mutation, capability creation or governance influence is blocked.
- Incident lifecycle is forward-only: `open -> acknowledged -> resolved -> archived`.
- Evidence/surface coupling is deterministic and fail-closed.

## Non-scope

- No runtime authority expansion.
- No governance logic change.
- No enforcement behavior change.
- No autonomous policy interpretation.
- No dynamic registry mutation.
- No automatic drift correction.
