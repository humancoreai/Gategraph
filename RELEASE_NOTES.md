# Release Notes – v0.9.0_CANDIDATE

## Purpose

v0.9.0_CANDIDATE is a milestone release candidate for external review. It consolidates the v0.8.x governance/enforcement line into a reproducible, reviewable baseline.

## Added

- External review bundle (`EXTERNAL_REVIEW.md`, `ARCHITECTURE.md`, `INVARIANTS.md`, `NON_SCOPE.md`).
- Deterministic release content rules (`RELEASE_CONTENT_RULES.md`).
- Release metadata and manifest files.
- Deterministic packaging and verification tools.
- `milestone_release_evidence` for package and documentation consistency checks.

## Unchanged

- Governance decision logic.
- Enforcement ordering.
- Runtime/session budget guard semantics.
- Audit append-only model.
- Replay and drift-detection semantics.

## Explicitly out of scope

- New risk models.
- Adaptive or autonomous policy updates.
- Machine-learning prediction.
- Self-healing governance.
- Dashboard/UI expansion.
- Multi-node/distributed operation.
