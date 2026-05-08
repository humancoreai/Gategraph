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
