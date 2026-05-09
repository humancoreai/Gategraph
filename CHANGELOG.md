# Changelog

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

## v0.9.2_CANDIDATE

- Added Multi-Agent SSOT, Multi-Mode SSOT, Delegation Boundary, Budget Authority, Replay/Audit, and Emergence Boundaries documents.
- Added multi_agent_architecture_evidence to verify boundary claims.
- No governance logic, runtime execution, risk model, autonomous agent, or distributed governance change.
