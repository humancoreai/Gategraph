# Release Status — GateGraph v0.8.28_STABLE

## Status

Stable release.

`v0.8.28_STABLE` promotes the governance-documentation candidate after full Windows Evidence CI passed.

## Stable scope

- Root-level `GOVERNANCE.md` added as repository-level governance SSOT.
- README references governance document.
- Version/release metadata updated.
- No functional code changes from `v0.8.27.1_STABLE` / `v0.8.28_CANDIDATE`.

## Validation

Full Windows Evidence CI on `v0.8.28_CANDIDATE`:

```text
Passed: True
Unexpected Allows: 0
Invariant Violations: 0
Date: 2026-04-28
```

## Production boundary

Still not production-ready for open distributed use. Remaining boundaries:

- Single-node only
- No production KMS
- No distributed budget lock/consensus
- Mock external API integration only
- No production monitoring/alerting stack
- No automated incident recovery

## Stable release document

See `docs/RELEASE_v0.8.28_STABLE.md`.
