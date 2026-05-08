# Release Notes – v0.10.0_CANDIDATE

## Summary

v0.10.0_CANDIDATE is a runtime/boundary hardening candidate. It does not add features. It makes the existing trusted-entry assumption executable before Governance can classify risk, evaluate rules, reserve budget, write audit events, or issue capability tokens.

## Added

- `src/runtime_path_assertions.py`
- `docs/RUNTIME_BOUNDARY_HARDENING.md`
- `tests/runtime_boundary_hardening_evidence.py`

## Changed

- `src/governance.py` now requires a trusted entry context before evaluation proceeds.
- `src/service_adapter.py` supplies the trusted production context after caller-boundary validation.
- `tests/evidence_ci.py` includes runtime boundary hardening evidence and marks legacy direct Governance evidence with an explicit test-only compatibility path.

## Unchanged

- governance decision logic
- risk model
- rule model
- runtime execution model
- token semantics
- adapter surface
- agent behavior
