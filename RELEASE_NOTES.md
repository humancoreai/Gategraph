# Release Notes – v0.10.1_STABLE

## Summary

v0.10.1_STABLE continues Phase A: Runtime / Boundary Hardening. It makes the internal/public API boundary explicit and adds executable evidence for forbidden runtime entry paths and freeze-aware runtime invariants.

## Added

- `src/api_boundary.py`
- `tests/api_boundary_split_evidence.py`
- `tests/freeze_runtime_invariant_evidence.py`

## Changed

- `runtime_path_assertions` now delegates component classification to the explicit API boundary classifier.
- Trusted entry audit data now records the boundary class.
- Release metadata and release build tooling now target `v0.10.1_STABLE`.

## Unchanged

- governance decisions
- enforcement rules
- risk model
- budget model
- adapter surface
- agent boundary model

## Release intent

Make forbidden governance entry paths executable and testable without adding runtime capability or new integrations.
