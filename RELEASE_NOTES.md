# GateGraph v0.13.3_CANDIDATE Release Notes

Status: candidate.
Base: v0.13.2_STABLE.

## Scope

Evidence Suite Profile Management.

This candidate adds a descriptive registry and evidence check for CI evidence suite profile management. It does not remove tests, alter governance logic, change runtime behavior, or grant automatic pruning authority.

## Added

- `docs/EVIDENCE_SUITE_PROFILE.md`
- `registry/evidence_suite_profile.json`
- `tests/evidence_suite_profile_evidence.py`

## Release / Semantic Registry surfaces

The release keeps the existing Semantic Registry, Registry Lock, Release Surface, Recovery, Replay, Schema, Provenance, and Governance Lineage evidence surfaces visible in the release notes so `evidence_surface_consistency_evidence` can verify that the CI manifest, files, and release notes remain synchronized.

Referenced evidence surfaces:

- `candidate_stable_surface_parity_evidence`
- `cross_registry_integrity_evidence`
- `dependency_visibility_evidence`
- `deterministic_export_contract_evidence`
- `evidence_provenance_registry_evidence`
- `evidence_surface_consistency_evidence`
- `freeze_snapshot_determinism_evidence`
- `governance_lineage_snapshot_evidence`
- `governance_mutation_visibility_evidence`
- `incident_lifecycle_consistency_evidence`
- `invariant_surface_mapping_evidence`
- `promotion_surface_symmetry_evidence`
- `release_manifest_coverage_evidence`
- `release_state_transition_evidence`
- `replay_provenance_consistency_evidence`
- `schema_drift_visibility_evidence`
- `schema_governance_evidence`
- `semantic_drift_detection_evidence`
- `semantic_registry_evidence`
- `semantic_registry_lock_evidence`

## Invariants

- Evidence profiles are descriptive only.
- Core release/security gates remain mandatory.
- No automatic test pruning or promotion authority is introduced.
- Candidate-to-Stable promotion still requires Windows CI `Passed: True`.
- No governance logic change.
- No runtime/enforcement behavior change.
- No autonomous policy update.
- No semantic scoring or memory system.
