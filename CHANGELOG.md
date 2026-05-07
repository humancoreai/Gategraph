# Changelog

## v0.11.1_STABLE

- Added release-process guard for Candidate/Stable metadata consistency.
- Added structured manifest validation and stale/missing manifest detection.
- Added dead local markdown reference checks.
- No runtime, governance, enforcement, adapter, packaging, or UI behavior changed.

## v0.10.2_STABLE

- Added runtime chain/order assertions.
- Added skipped-stage and invalid enforcement-chain detection evidence.
- Tied freeze-aware invariant evidence further to executable runtime behavior.

## v0.10.1_STABLE

- Added explicit public/internal/forbidden API boundary classification.
- Added runtime path assertion coverage for forbidden governance entry paths.

## v0.10.0_STABLE

- Added TrustedEntryContext enforcement for direct governance entry.
- Direct `governance.evaluate_task()` calls without trusted context fail closed by default.


All notable changes to GateGraph are documented here.

## [v0.9.1_STABLE] - 2026-05-06

### Added

- `TRUST_MODEL.md` documenting caller trust boundaries and non-goals.
- Caller boundary validation evidence.
- Release integrity evidence for manifest, ZIP reproducibility, and verifier repeatability.
- `CONTRIBUTING.md`, `RELEASE_PROCESS.md`, `LICENSE`, and updated `SECURITY.md` for external review readiness.

### Changed

- Public adapter boundary now requires explicit `input_source`, `data_sensitivity`, and `secrets_involved` fields.
- Release build and verification scripts now fail closed on empty manifests, forbidden artifacts, undeclared files, and manifest/ZIP mismatch.
- Version metadata updated for v0.9.1 candidate scope.

### Not Changed

- No new governance decision logic.
- No new runtime guard.
- No new risk model.
- No autonomous or semantic classification.
- No multi-node behavior.

## [v0.9.0_CANDIDATE] - 2026-05-06

### Added

- External review baseline.
- Release manifest and metadata.
- Deterministic release packaging tooling.
- Scope freeze and non-scope documentation.

## v0.9.2_STABLE

- Added Multi-Agent SSOT, Multi-Mode SSOT, Delegation Boundary, Budget Authority, Replay/Audit, and Emergence Boundaries documents.
- Added multi_agent_architecture_evidence to verify boundary claims.
- No governance logic, runtime execution, risk model, autonomous agent, or distributed governance change.
