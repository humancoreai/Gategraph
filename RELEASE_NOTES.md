# Release Notes

## v0.8.36_STABLE

Stable release for API Robustness / Real-World Stability.

Promotion basis: Full Windows Evidence CI passed, including api_contract_evidence, api_robustness_evidence, server_hardening_evidence, and repo_push_hygiene_evidence.

Invariants preserved: API contract unchanged, no new response fields, no core governance changes, server remains adapter-only.


## v0.8.34_STABLE

Server Hardening / Safe Service Boundary release.

Stable promotion from `v0.8.34_CANDIDATE` after Full Windows Evidence CI passed.

### Added / hardened

- `tests/server_hardening_evidence.py` added to aggregate evidence CI.
- Server request boundary validates content type, JSON parsing, body size and required fields before calling `service_adapter`.
- Deterministic JSON error schema for server boundary failures.
- Unsupported methods and unknown endpoints fail closed with JSON responses.
- Default server bind remains `127.0.0.1`; explicit public bind emits an operator warning.
- `/status` and `/monitoring` remain read-only observation endpoints.

### Invariants preserved

- Server remains an adapter.
- CLI and Server continue to use `src/service_adapter.py`.
- No new governance rules.
- No new runtime policy.
- No background actions.
- No external actions added.

### Evidence

- Full Windows Evidence CI: passed.
- `server_mode_evidence`: passed.
- `server_hardening_evidence`: passed.

# RELEASE_NOTES

## v0.8.33_STABLE

- Promoted v0.8.33_CANDIDATE to Stable after target-environment Windows Evidence CI passed.
- Added minimal Server Mode / Integration Layer:
  - `POST /evaluate`
  - `GET /status`
  - `GET /monitoring`
- Added shared `src/service_adapter.py` so CLI and Server use the same Core/Governance path.
- Added `src/server.py` as adapter-only HTTP entry point.
- Added server mode documentation and evidence coverage.
- Hardened CLI mode boundary:
  - CLI supports only `mode: single_node`
  - unsupported modes fail closed with structured JSON error and non-zero exit code
- No new autonomy, background actions, rule mutation, or Governance-Core bypass introduced.


## v0.8.32_STABLE

- Added `export-monitoring` CLI command.
- Writes a structured `monitoring.json` from existing Operational state.
- Export is read-only for Governance, Runtime, Budget, Policy and Incident state.
- Added single-node monitoring export evidence.
- No changes to Governance, Enforcement, Runtime Guard, Budget Ledger, HTTP Policy, Secret Handling, or Operational decision logic.
- Full Windows Evidence CI passed.

## v0.8.31_CANDIDATE

- Added single-node CLI adapter (`python -m src.cli`).
- Added dependency-free config loader for YAML/JSON config.
- Added example config and task files.
- Added single-node CLI evidence.
- No changes to Governance, Enforcement, Runtime Guard, Budget Ledger, HTTP Policy, Secret Handling, or Operational logic.
- Full Windows Evidence CI passed.


## v0.8.40_CANDIDATE

- Added read-only operator control layer.
- Added operator evidence test.
- No core behavior changes.
## v0.8.42_CANDIDATE

- Added static Operator Workflow / Playbook layer.
- Added descriptive playbook matching by reason code and guard.
- Added operator workflow JSONL documentation events.
- Added Incident/Pattern to Playbook reference linking.
- Added reproducible workflow snapshot helper.
- Added operator_workflow_evidence to Evidence CI manifest.
- No Governance, Enforcement, Runtime, Budget or Audit logic changed.

## v0.8.42_STABLE

Stable promotion from `v0.8.42_CANDIDATE` after Full Windows Evidence CI passed on 2026-05-06.

- Added Operator Workflow / Playbook layer.
- Kept implementation read-only and descriptive.
- Preserved existing governance, enforcement, runtime, and audit behavior.



## v0.8.44_CANDIDATE — Governance Drift Detection

- Added descriptive governance baseline snapshots.
- Added descriptive snapshot comparison across reason, guard, queue and workflow distributions.
- Added append-only drift event records.
- Added queue/reason co-occurrence view and workflow distribution snapshot.
- Added `drift_detection_evidence`.
- No governance decision, policy, guard or queue mutation introduced.

## v0.8.44_STABLE — Governance Drift Detection

Stable promotion from `v0.8.44_CANDIDATE` after Full Windows Evidence CI passed on 2026-05-06.

- Added descriptive governance baseline snapshots.
- Added descriptive snapshot comparison across reason, guard, queue and workflow distributions.
- Added append-only drift event records.
- Added queue/reason co-occurrence view and workflow distribution snapshot.
- Added `drift_detection_evidence` to Evidence CI.
- Preserved read-only/descriptive behavior: no severity, risk level, recommendations, escalation, policy changes, queue mutation or governance decision changes.



## v0.8.45_STABLE — Governance Archive / Historical Replay

Stable promotion from `v0.8.45_CANDIDATE` after Full Windows Evidence CI passed on 2026-05-06.

- Added append-only governance archive records.
- Added historical replay by archived record ID.
- Added payload hash verification for replayed records.
- Added `governance_archive_replay_evidence` to Evidence CI.
- Preserved replay-only behavior: no re-evaluation, no policy changes, no guard mutation, no queue mutation and no runtime decision changes.


## v0.8.46_CANDIDATE - Archive Integrity / Replay Consistency

This candidate adds a descriptive integrity layer for archived governance records and historical replay. It verifies archive envelope consistency, payload hash observations, record id observations and deterministic replay reconstruction without changing governance decisions.


## v0.8.46_STABLE - Archive Integrity / Replay Consistency

- Stable after Windows Full Evidence CI passed.
- Archive integrity and replay consistency accepted as v0.8.46 stable baseline.


## v0.8.47_CANDIDATE - Operator Export / Evidence Bundle

- Adds deterministic, read-only evidence bundle creation for operator handoff.
- Adds bundle manifest hashing and source file observations.
- Adds operator_export_evidence to Evidence CI.
- No governance re-evaluation, policy tuning, prioritization or recommendation behavior.


## v0.8.47_STABLE - Operator Export / Evidence Bundle

- Stable after Windows Full Evidence CI passed.
- Operator export/evidence bundle accepted as v0.8.47 stable baseline.
- No governance re-evaluation, policy tuning, prioritization or recommendation behavior.
