# GateGraph v0.12.9_CANDIDATE Release Notes

Base: v0.12.8_STABLE

Status: candidate

Scope: Governance Integrity Graph.

## Evidence added

- `governance_integrity_graph_evidence`
- `orphan_governance_artifact_evidence`
- `governance_impact_visibility_evidence`
- `integrity_graph_freeze_evidence`
- `deterministic_governance_diff_evidence`

## Added

- Declarative Governance Integrity Graph registry.
- Canonical edge types: `depends_on`, `validated_by`, `affects`, `lineage_of`.
- Orphan detection for governance graph nodes and validators.
- Descriptive impact visibility for freeze/replay affected surfaces.
- Deterministic integrity graph freeze hash.
- Deterministic governance diff from v0.12.8_STABLE to v0.12.9_CANDIDATE.

## Boundary invariants

- Integrity graph is descriptive only.
- Integrity graph does not grant runtime authority.
- Integrity graph does not mutate governance, policy, registries, schemas or evidence.
- No auto-repair, self-healing, dynamic loading or distributed consensus.
- Existing runtime, enforcement and governance decision logic unchanged.

## Carried forward active evidence gates

- `release_state_transition_evidence`
- `promotion_surface_symmetry_evidence`
- `candidate_stable_surface_parity_evidence`
- `evidence_provenance_registry_evidence`
- `governance_lineage_snapshot_evidence`
- `dependency_visibility_evidence`
- `governance_mutation_visibility_evidence`
- `replay_provenance_consistency_evidence`
- `semantic_registry_evidence`
- `semantic_registry_lock_evidence`
- `schema_governance_evidence`
- `cross_registry_integrity_evidence`
- `freeze_snapshot_determinism_evidence`

Compatibility note: No runtime/enforcement behavior change.
Compatibility note: No autonomous governance mutation.
Compatibility note: No semantic scoring or memory system.

Carried forward compatibility: Semantic Registry remains locked and descriptive-only.
No governance logic change.
No autonomous policy update.

Additional carried-forward evidence surface names:
- `deterministic_export_contract_evidence`
- `evidence_surface_consistency_evidence`
- `incident_lifecycle_consistency_evidence`
- `invariant_surface_mapping_evidence`
- `release_manifest_coverage_evidence`
- `schema_drift_visibility_evidence`
- `semantic_drift_detection_evidence`
