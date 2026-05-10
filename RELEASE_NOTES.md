# GateGraph v0.13.0_STABLE Release Notes

Base: v0.12.9_STABLE

Status: stable

Scope: Release Consistency Hardening.

## Added

- Release claim consistency evidence across metadata, notes, status, README, changelog and release document.
- Explicit `release_claim_consistency_scope` marker in release metadata.
- Stable release document for v0.13.0.

## Boundary invariants

- No runtime, enforcement or governance decision logic change.
- No new adapter, autonomous repair, policy mutation or self-promotion path.
- Evidence is descriptive and release-surface-only.
- Stable promotion completed after Windows CI passed.

## Carried forward active evidence surfaces

- Release process guard.
- Version and surface consistency checks.
- Recovery and registry surface checks.
- Semantic registry lock checks.
- Governance integrity graph checks.

Compatibility note: v0.13.0_STABLE is a release-hygiene stable built from v0.12.9_STABLE.

Carried forward: Semantic Registry lock and recovery surface checks remain active.

## Explicit semantic boundary claims

- No governance logic change.
- No runtime/enforcement behavior change.
- No autonomous policy update.
- No semantic scoring or memory system.

## Explicit evidence surface list

- `candidate_stable_surface_parity_evidence`
- `promotion_surface_symmetry_evidence`
- `release_state_transition_evidence`
- `replay_provenance_consistency_evidence`
- `governance_mutation_visibility_evidence`
- `dependency_visibility_evidence`
- `governance_lineage_snapshot_evidence`
- `evidence_provenance_registry_evidence`
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
