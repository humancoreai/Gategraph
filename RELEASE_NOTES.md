# Release Notes — GateGraph v0.8.29_STABLE

## Summary

`v0.8.29_STABLE` adds read-only Operational Alerting on top of existing append-only operational incidents and promotes the candidate after a full passing Windows Evidence CI run.

## Changes

- Added `OperationalAlert` signal model.
- Added deterministic alert evaluation for open incidents.
- Added severity-based alert ordering.
- Added targeted evidence that alerting does not mutate budget state or repair drift.
- Added operational alerting documentation and stable release document.

## Validation

- Full Windows Evidence CI: passed.
- `operational_alerting_evidence`: 4/4 passed.
- Unexpected allows: 0.
- Invariant violations: 0.

## Boundary

No enforcement behavior changed. No automatic recovery or monitoring transport was added.
