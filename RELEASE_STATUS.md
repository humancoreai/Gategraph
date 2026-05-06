# Release Status — GateGraph v0.8.28_CANDIDATE

## Status

Candidate release.

`v0.8.28_CANDIDATE` adds `GOVERNANCE.md` as the repository-level SSOT for GateGraph governance principles.

## Candidate scope

- Root-level `GOVERNANCE.md` added.
- README references governance document.
- Version/release metadata updated.
- No functional code changes.

## Validation baseline

Baseline inherited from `v0.8.27.1_STABLE`:

```text
Passed: True
Unexpected Allows: 0
Invariant Violations: 0
```

## Production boundary

Still not production-ready for open distributed use. Remaining boundaries:

- Single-node only
- No production KMS
- No distributed budget lock/consensus
- Mock external API integration only
- No production monitoring/alerting stack
- No automated incident recovery

## Candidate release document

See `docs/RELEASE_v0.8.28_CANDIDATE.md`.
