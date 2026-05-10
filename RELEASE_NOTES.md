# Release Notes – v0.11.0_CANDIDATE

## Summary

v0.11.0_CANDIDATE starts Phase B: Deployment / Packaging Baseline.

This release makes GateGraph locally installable and standardizes the supported single-node deployment surface. It does not change governance, enforcement, runtime, adapter, token, budget, audit, or chain-order behavior.

## Added

- `pyproject.toml`
- `docs/DEPLOYMENT_BOUNDARY.md`
- `tests/packaging_integrity_evidence.py`
- `tests/install_surface_evidence.py`

## Packaging scope

- editable local install with `pip install -e .`
- console scripts mapped to existing modules
- package metadata aligned with release metadata
- source package excludes runtime artifacts through release hygiene

## Unchanged

- governance logic
- enforcement logic
- runtime logic
- service adapter behavior
- capability-token model
- risk/rule engines
- session/runtime/flood guards
- audit/replay model
- UI scope
