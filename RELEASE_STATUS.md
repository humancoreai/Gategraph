# Release Status — GateGraph v0.8.29_CANDIDATE

## Status

Candidate release.

`v0.8.29_CANDIDATE` starts the Operational Gate after `v0.8.28_STABLE`.

## Candidate scope

- Adds read-only operational alert evaluation.
- Converts open operational incidents into sorted alert signals.
- Keeps Operational Layer observational only.
- Adds targeted evidence for alert generation and non-mutation.

## Validation

Targeted evidence in this environment:

```text
operational_alerting_evidence: 4/4 passed
```

Full Evidence CI was attempted but did not complete in this Linux container because the existing runner selftest hangs here. Windows full Evidence CI remains the required promotion gate, as in prior releases.

## Production boundary

Still not production-ready for open distributed use. Remaining boundaries:

- Single-node only
- No production KMS
- No distributed budget lock/consensus
- Mock external API integration only
- No production monitoring transport
- No automated incident recovery

## Candidate release document

See `docs/RELEASE_v0.8.29_CANDIDATE.md`.
