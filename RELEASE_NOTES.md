
## v0.14.3_CANDIDATE

Phase: Install / Packaging / Public Repo Hygiene
Base: v0.14.2_STABLE
Status: candidate

Scope:
- Public-repo and packaging hygiene surface.
- Deterministic quickstart/install guidance.
- README and release-surface consistency checks.
- No governance, runtime, enforcement, policy, or agentic behavior changes.

Evidence added:
- public_repo_hygiene_evidence.py

# GateGraph v0.14.3_CANDIDATE Release Notes

Status: candidate.
Base: v0.14.2_STABLE.

## Scope

Install / Packaging / Public Repo Hygiene.

This stable release preserves a minimal GitHub Actions validation surface for Windows Evidence CI. It does not remove tests, alter governance logic, change runtime behavior, access secrets, publish artifacts, deploy, or grant automatic repair/promotion authority.

## Added

- `.github/workflows/evidence_ci.yml`
- `docs/GITHUB_ACTIONS_CI.md`
- `tests/github_actions_ci_evidence.py`

## Release / Semantic Registry surfaces

The release keeps the existing Semantic Registry, Registry Lock, Release Surface, Recovery, Replay, Schema, Provenance, Governance Lineage, and Evidence Suite Profile surfaces visible in the release notes so evidence surface checks can verify that the CI manifest, files, and release notes remain synchronized.

Referenced evidence surfaces:

- `evidence_runner_selftest`
- `runtime_stress_evidence`
- `session_budget_evidence`
- `guard_orchestration_evidence`
- `reason_normalization_evidence`
- `scale_safety_evidence`
- `external_api_evidence`
- `runaway_cost_evidence`
- `runtime_cost_governance_evidence`
- `observability_evidence`
- `failure_analysis_evidence`
- `operator_workflow_evidence`
- `human_review_queue_evidence`
- `drift_detection_evidence`
- `governance_archive_replay_evidence`
- `archive_integrity_replay_consistency_evidence`
- `operator_export_evidence`
- `final_consolidation_evidence`
- `governance_freeze_evidence`
- `milestone_release_evidence`
- `caller_boundary_evidence`
- `runtime_boundary_hardening_evidence`
- `api_boundary_split_evidence`
- `freeze_runtime_invariant_evidence`
- `runtime_chain_order_evidence`
- `release_integrity_evidence`
- `release_process_guard_evidence`
- `packaging_integrity_evidence`
- `release_content_hygiene_evidence`
- `install_surface_evidence`
- `config_consistency_evidence`
- `startup_surface_evidence`
- `startup_shutdown_semantics_evidence`
- `runtime_surface_consistency_evidence`
- `surface_freeze_coupling_evidence`
- `mode_boundary_surface_evidence`
- `multi_agent_architecture_evidence`
- `multi_agent_delegation_boundary_evidence`
- `context_poisoning_evidence`
- `instruction_data_separation_evidence`
- `context_provenance_evidence`
- `context_lifecycle_evidence`
- `context_replay_explain_boundary_evidence`
- `context_freeze_coupling_evidence`
- `recovery_foundation_evidence`
- `replay_recovery_consistency_evidence`
- `surface_recovery_consistency_evidence`
- `recovery_idempotency_evidence`
- `replay_order_determinism_evidence`
- `recovery_surface_registry_evidence`
- `release_surface_sync_evidence`
- `release_claim_consistency_evidence`
- `recovery_replay_finality_evidence`
- `replay_reference_integrity_evidence`
- `version_consistency_evidence`
- `surface_contract_registry_evidence`
- `semantic_boundary_evidence`
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
- `evidence_provenance_registry_evidence`
- `governance_lineage_snapshot_evidence`
- `dependency_visibility_evidence`
- `governance_mutation_visibility_evidence`
- `replay_provenance_consistency_evidence`
- `release_state_transition_evidence`
- `candidate_ci_gate_evidence`
- `evidence_suite_profile_evidence`
- `promotion_surface_symmetry_evidence`
- `candidate_stable_surface_parity_evidence`
- `governance_integrity_graph_evidence`
- `orphan_governance_artifact_evidence`
- `governance_impact_visibility_evidence`
- `integrity_graph_freeze_evidence`
- `deterministic_governance_diff_evidence`
- `root_surface_hygiene_evidence`
- `governance_semantics_evidence`
- `operator_evidence`
- `cross_session_budget_evidence`
- `operational_hardening_evidence`
- `operational_alerting_evidence`
- `operational_stability_evidence`
- `single_node_cli_evidence`
- `single_node_monitoring_export_evidence`
- `server_mode_evidence`
- `server_hardening_evidence`
- `api_contract_evidence`
- `api_robustness_evidence`
- `repo_push_hygiene_evidence`
- `capability_token_hardening_evidence`
- `capability_token_redaction_evidence`
- `token_exposure_evidence`
- `key_rotation_evidence`
- `secret_api_integration_evidence`
- `http_policy_evidence`
- `security_finesse_evidence`
- `block_c_stress_evidence`
- `block_d_audit_explain_evidence`
- `core_loop`
- `runtime_guard`
- `pattern_engine`
- `pattern_intelligence`
- `usage_simulation`
- `unusual_inputs`
- `agent_scenarios`
- `controlled_apply`
- `evidence_failure_classification_evidence`
- `release_gate_robustness_evidence`

## Invariants

- Release gate robustness is descriptive only.
- No automatic repair.
- No automatic test pruning.
- Core release/security gates remain mandatory.
- Candidate-to-Stable promotion still requires Windows CI `Passed: True`.
- No governance logic change.
- No runtime/enforcement behavior change.
- No autonomous policy update.
- No semantic scoring or memory system.


## v0.14.3 candidate scope

- Practical single-node scenario evidence added as deterministic local validation.
- No ad-hoc stress report is integrated into release surfaces.
- No governance, runtime, enforcement, policy-learning, deployment, or auto-promotion authority added.
