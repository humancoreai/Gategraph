# Release Status — GateGraph v0.8.29_STABLE

## Status

Stable release.

`v0.8.29_STABLE` promotes `v0.8.29_CANDIDATE` after successful full Windows Evidence CI.

## Stable scope

- Adds read-only operational alert evaluation.
- Converts open operational incidents into sorted alert signals.
- Keeps Operational Layer observational only.
- Adds targeted evidence for alert generation and non-mutation.

## Validation

Full Windows Evidence CI:

```text
CI EVIDENCE REPORT
Passed: True
```

Targeted evidence:

```text
operational_alerting_evidence: 4/4 passed
```

No unexpected allows and no invariant violations were reported in the full evidence run.

## Production boundary

Still not production-ready for open distributed use. Remaining boundaries:

- Single-node only
- No production KMS
- No distributed budget lock/consensus
- Mock external API integration only
- No production monitoring transport
- No automated incident recovery

## Stable release document

See `docs/RELEASE_v0.8.29_STABLE.md`.
