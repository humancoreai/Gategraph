# Release Notes — GateGraph v0.12.6_CANDIDATE

## v0.12.6_CANDIDATE — Deterministic Evidence Lineage / Governance Provenance

Base: v0.12.5_STABLE  
Status: candidate

### Added
- Evidence provenance registry for deterministic, read-only evidence origin and dependency visibility.
- Governance lineage snapshot registry for release-to-release provenance of declarative governance surfaces.
- Dependency visibility evidence for evidence-to-registry and evidence-to-manifest references.
- Governance mutation visibility evidence for descriptive lineage delta detection.
- Replay provenance consistency evidence linking replay reconstruction to release, schema and lineage state.

### Evidence gates
- `evidence_provenance_registry_evidence`
- `governance_lineage_snapshot_evidence`
- `dependency_visibility_evidence`
- `governance_mutation_visibility_evidence`
- `replay_provenance_consistency_evidence`

### Boundary invariants
- Provenance is descriptive only.
- Provenance does not grant runtime authority.
- Provenance does not mutate governance, policy, registry, schema, freeze or replay state.
- Dependency visibility does not load plugins or external resources.
- Replay provenance is reconstruction context only, not execution context.

### Non-scope
- No governance logic change.
- No enforcement behavior change.
- No runtime authority expansion.
- No distributed consensus.
- No dynamic plugin or loader system.
- No automatic migration or repair.

Compatibility note: No runtime/enforcement behavior change.
Compatibility note: No autonomous governance mutation.
Compatibility note: No semantic scoring or memory system.

### Carried forward active evidence gates
- `semantic_registry_evidence`
- `invariant_surface_mapping_evidence`
- `incident_lifecycle_consistency_evidence`
- `semantic_drift_detection_evidence`
- `evidence_surface_consistency_evidence`
- `semantic_registry_lock_evidence`
- `release_manifest_coverage_evidence`
- `schema_governance_evidence`
- `cross_registry_integrity_evidence`
- `deterministic_export_contract_evidence`
- `schema_drift_visibility_evidence`
- `freeze_snapshot_determinism_evidence`
Compatibility note: No autonomous policy update.
Compatibility note: Semantic Registry linkage remains active and locked.
