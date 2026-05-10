# Changelog

All notable changes to GateGraph are documented here.

## v0.11.2_STABLE

- Added runtime startup/shutdown semantics evidence.
- Added runtime surface consistency evidence.
- Added surface freeze coupling evidence.
- Added explicit runtime surface freeze and operational boundary tightening documentation.
- Hardened release-process guard coverage for changelog, known-gaps roadmap, and HTTP server version consistency.
- No runtime/governance/enforcement/adapter/agentic capability change.

## v0.11.1_STABLE

- Stabilized v0.11.1 packaging baseline after Windows Evidence CI PASS.
- Preserved install surface, startup surface, config consistency and deterministic packaging claims.
- No runtime, governance, enforcement, adapter, agentic, distributed, cloud, Docker/Kubernetes/Helm, or UI behavior changed.

## v0.11.1_CANDIDATE

- Tightened packaging/install/startup consistency around the v0.11.0 packaging baseline.
- Added supporting evidence for install surface, startup surface and config consistency.
- No runtime/governance/enforcement/adapter/agentic capability change.

## v0.11.0_STABLE

- Stabilized v0.11.0 packaging baseline after Windows Evidence CI PASS.
- Confirmed `pyproject.toml`, editable install and CLI entry points as release-supported surfaces.
- No runtime, governance, enforcement, adapter, agentic, distributed, cloud, Docker/Kubernetes/Helm, or UI behavior changed.

## v0.11.0_CANDIDATE

- Added `pyproject.toml` packaging baseline.
- Added package metadata for editable install via `python -m pip install -e .`.
- Added console entry points: `gategraph` and `gategraph-server`.
- Added packaging/install evidence without changing runtime/governance/enforcement behavior.

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
