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
