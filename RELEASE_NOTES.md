# RELEASE_NOTES

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
