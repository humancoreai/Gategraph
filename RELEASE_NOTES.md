# Release Notes — GateGraph v0.12.3_STABLE

## v0.12.3_STABLE — Semantic & Registry Consolidation

Base: v0.12.2_STABLE  
Status: stable

### Added
- Declarative semantic object registry for replay, explain, monitoring, proposal, archive, recovery snapshot and context reference objects.
- Invariant/surface/evidence mapping registry for semantic, incident and release-surface coupling.
- Forward-only incident lifecycle formalization including `archived` as terminal state.
- Deterministic semantic drift checks for authority, execution, runtime access, policy mutation and semantic promotion regressions.
- Evidence/surface consistency checks so new semantic evidence files are surfaced in CI, release notes and invariant mapping.

### Evidence gates
- `semantic_registry_evidence`
- `invariant_surface_mapping_evidence`
- `incident_lifecycle_consistency_evidence`
- `semantic_drift_detection_evidence`
- `evidence_surface_consistency_evidence`

### Boundary invariants
- Reference objects remain non-authoritative.
- Replay remains non-executable.
- Explain remains referential.
- Monitoring remains read-only.
- Proposal objects remain proposal-only.
- Semantic promotion remains blocked.
- Registry and surface mapping remain deterministic.
- Incident lifecycle is forward-only.

### Non-scope
- No governance logic change.
- No enforcement behavior change.
- No runtime authority expansion.
- No autonomous policy interpretation.
- No dynamic plugin or loader system.
- No automatic semantic drift correction.

Compatibility note: No runtime/enforcement behavior change.
Compatibility note: No autonomous policy update.
Compatibility note: No semantic scoring or memory system.
