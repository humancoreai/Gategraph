# Release Notes — GateGraph v0.8.30_STABLE

## Summary

v0.8.30_STABLE completes the Operational Stability Gate.

## Added

- Alert Aggregator for deterministic alert deduplication.
- Incident State Manager with manual forward-only lifecycle.
- Monitoring Export for read-only operational state reports.
- Actor-scoped deterministic Flood Guard.

## Fixed

- Updated runaway-cost evidence expectation for v0.8.30 guard order:
  invalid projected cost may fail closed at `flood_guard` before session reservation.

## Invariants

- Operational layer remains read-only.
- Flood Guard is a Governance guard, not an Operational decision.
- Blocked Flood Guard attempts do not reserve session budget.
- No autonomous recovery, no UI, no external monitoring integration.
