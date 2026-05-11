# Release — GateGraph v0.8.28_STABLE

## Status

Stable release.

This release promotes `v0.8.28_STABLE` after full Windows Evidence CI passed.

## Scope

- Added root-level `GOVERNANCE.md`.
- Added README reference to `GOVERNANCE.md`.
- Promoted governance-documentation consolidation to stable.

## Functional changes

None.

No runtime, enforcement, budget, token, HTTP, secret, audit, explain, pattern-engine, review-workflow or controlled-apply code was changed.

## Validation

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

This is the stable pre-operational baseline: governance is explicit, versioned and documented, while runtime behavior remains unchanged from the previously validated stable core.
