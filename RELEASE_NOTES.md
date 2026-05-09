# Release Notes — GateGraph v0.8.29_CANDIDATE

## Summary

`v0.8.29_CANDIDATE` adds read-only Operational Alerting on top of existing append-only operational incidents.

## Changes

- Added `OperationalAlert` signal model.
- Added deterministic alert evaluation for open incidents.
- Added severity-based alert ordering.
- Added targeted evidence that alerting does not mutate budget state or repair drift.
- Added operational alerting documentation and release document.

## Validation

- `operational_alerting_evidence`: 4/4 passed.

## Boundary

No enforcement behavior changed. No automatic recovery or monitoring transport was added.
