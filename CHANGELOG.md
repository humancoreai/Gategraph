# Changelog

## v0.12.1_CANDIDATE

- Adds Governance Surface Freeze candidate scope.
- Adds descriptive contract registry for governance decision, normalized reason, monitoring export and capability token claim surfaces.
- Adds surface contract registry and semantic boundary evidence.
- No governance, runtime or enforcement authority change.

## v0.12.0_STABLE

### Review hygiene fix
- Align README base-stable claim with `v0.12.0_STABLE`.
- Document canonical namespace boundary for `src/` versus `gategraph/context/`.
- Exclude development STARTPROMPT artifacts from release packaging.
- Surface `OWASP_AGENTIC_AI_MAPPING.md` in README.

- Added descriptive context lifecycle coupling around the v0.11.7 context governance boundary.
- Added fail-closed lifecycle state and transition validation.
- Added explicit replay/explain/proposal rehydration blocking.
- Added `gategraph/context/context_lifecycle.py`, `docs/CONTEXT_LIFECYCLE_MODEL.md`, and lifecycle/freeze evidence.
- No memory system, vector database, semantic scoring, autonomous filtering, adaptive trust, AI moderation, governance rule, enforcement authority, runtime mode, adapter authority, distributed, cloud, Docker/Kubernetes, or UI scope expansion.

- Added deterministic context classification and required provenance boundaries.
- Added instruction/data separation for untrusted, replay and proposal context.
- Added replay/explain hardening markers: descriptive-only, non-executable and reference-context.
- Added visibility-only suspicious context markers for hidden instructions, fake operator claims, recursive delegation phrases and embedded authority patterns.
- Added context governance evidence suites and `CONTEXT_GOVERNANCE_MODEL.md`.
- No memory system, vector database, semantic scoring, autonomous filtering, AI moderation, governance rule, enforcement authority, runtime mode, adapter authority, distributed, cloud, Docker/Kubernetes, or UI scope expansion.

All notable changes to GateGraph are documented here.


## v0.11.4_STABLE

- Added capability-token audit redaction invariant.
- Added audit-safe token references with `token_id` and `token_hash`.
- Added `capability_token_redaction_evidence.py` to block raw token/signature/auth material in audit events.
- Added `docs/CAPABILITY_TOKEN_AUDIT_REDACTION.md`.
- No Governance decision model, Runtime Guard behavior, Enforcement rule, budget policy, secret resolution, HTTP policy, adapter authority, agentic behavior, distributed governance, deployment, or UI capability change.

## v0.11.3_STABLE

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
- Version metadata updated for v0.9.1 stable scope.

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
