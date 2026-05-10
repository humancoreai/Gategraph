# Release — GateGraph v0.8.28_CANDIDATE

## Status

Candidate release.

This candidate integrates `GOVERNANCE.md` as the repository-level SSOT for GateGraph governance principles.

## Scope

- Added root-level `GOVERNANCE.md`.
- Added README reference to `GOVERNANCE.md`.
- Updated version/release metadata to `v0.8.28_CANDIDATE`.

## Functional changes

None.

No runtime, enforcement, budget, token, HTTP, secret, audit, explain, pattern-engine, review-workflow or controlled-apply code was changed.

## Validation baseline

This candidate inherits the `v0.8.27.1_STABLE` validation baseline:

```text
Full Windows Evidence CI: Passed: True
Unexpected Allows: 0
Invariant Violations: 0
Date: 2026-04-28
```

## Known boundaries

- Single-node only.
- No production KMS.
- No distributed budget lock/consensus.
- Mock external API integration only.
- No production monitoring/alerting stack.
- No automated incident recovery.

## Release interpretation

This is a documentation/governance consolidation step, not a feature expansion.
