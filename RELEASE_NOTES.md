# Release Notes — GateGraph v0.12.4_STABLE

## v0.12.4_STABLE — Semantic Registry Lock & Coverage Freeze

Base: v0.12.3_STABLE  
Status: stable

### Added
- Deterministic semantic registry lock for `semantic_object_types.json` and `invariant_surface_registry.json`.
- Registry hash validation that detects silent semantic/surface registry mutation.
- Release manifest coverage evidence for registry-lock files and related evidence surfaces.
- Explicit lock boundary flags: non-authoritative, non-executable, no runtime access, no policy mutation, no dynamic loading and no auto-repair.

### Evidence gates
- `semantic_registry_lock_evidence`
- `release_manifest_coverage_evidence`
- Existing semantic registry, invariant surface, incident lifecycle, drift and evidence surface checks remain active:
  - `semantic_registry_evidence`
  - `invariant_surface_mapping_evidence`
  - `incident_lifecycle_consistency_evidence`
  - `semantic_drift_detection_evidence`
  - `evidence_surface_consistency_evidence`

### Boundary invariants
- Registry locks are release evidence only.
- Registry locks do not grant runtime authority.
- Registry locks do not dynamically load files or plugins.
- Registry locks do not auto-repair semantic drift.
- Registry hash mismatch is visible and fail-closed in evidence.

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
