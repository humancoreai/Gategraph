# Release Notes — GateGraph v0.12.0_CANDIDATE

Base: `v0.11.9_STABLE`

## Purpose

`v0.12.0_CANDIDATE` starts the Governance Surface Freeze phase. It adds a minimal contract registry for core governance surfaces and evidence that checks those surfaces for deterministic schema/version drift.

## Added

- `contracts/` registry for descriptive surface contracts.
- `tests/surface_contract_registry_evidence.py` for required contract presence, field/type shape, schema version and release metadata coupling.
- `tests/semantic_boundary_evidence.py` for non-executable/read-only semantic boundary guarantees around contracts and monitoring/explain surfaces.
- `docs/GOVERNANCE_SURFACE_FREEZE.md` to define scope and non-scope.

## Non-scope

- No governance logic change.
- No runtime/enforcement behavior change.
- No autonomous policy update.
- No semantic scoring or memory system.
- No external validator dependency.

## Evidence expectation

Run:

```powershell
python tests\evidence_ci.py
```
