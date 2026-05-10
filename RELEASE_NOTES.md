# GateGraph v0.13.1_CANDIDATE Release Notes

Base: v0.13.0_STABLE

Status: candidate

Scope: Recovery Replay Finality Hardening.

## Added

- Recovery/replay finality evidence for duplicate recovery attempts, consumed/released reservation finality, conflicting audit-derived finality, and recovery snapshot reference-only behavior.
- `docs/RECOVERY_REPLAY_FINALITY.md` as the bounded release-surface explanation for this phase.
- Explicit `recovery_replay_finality_scope` marker in release metadata.

## Boundary invariants

- No runtime, enforcement or governance decision logic change.
- No autonomous repair, replay-to-runtime rehydration, policy mutation, capability creation or self-promotion path.
- Recovery/replay objects remain descriptive/reference-only.
- Candidate requires Windows CI before stable promotion.

## Carried forward active evidence surfaces

- Release process guard.
- Version and surface consistency checks.
- Recovery and registry surface checks.
- Semantic registry lock checks.
- Governance integrity graph checks.

Compatibility note: v0.13.1_CANDIDATE is a recovery/replay evidence hardening candidate built from v0.13.0_STABLE.

Carried forward: Semantic Registry lock and recovery surface checks remain active.

## Explicit semantic boundary claims

- No governance logic change.
- No runtime/enforcement behavior change.
- No autonomous policy update.
- No semantic scoring or memory system.

## Explicit evidence surface list

- `recovery_replay_finality_evidence`
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
