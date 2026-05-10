# Release Notes — GateGraph v0.12.1_CANDIDATE

## v0.12.1_CANDIDATE — Consistency / Recovery Foundation

Base: v0.12.0_STABLE  
Status: candidate

### Added
- Descriptive recovery foundation for interrupted reservation, duplicate consume, partial audit append, incident forward-only lifecycle, and deterministic replay signatures.
- Evidence gates: `recovery_foundation_evidence`, `replay_recovery_consistency_evidence`, `surface_recovery_consistency_evidence`.

### Non-scope
- No automatic repair, no policy mutation, no new adapter, no runtime authority expansion, no distributed recovery.


Base: `v0.12.0_STABLE`

## Purpose

`v0.12.1_CANDIDATE` promotes the Governance Surface Freeze phase to stable. It adds a minimal contract registry for core governance surfaces and evidence that checks those surfaces for deterministic schema/version drift.

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
