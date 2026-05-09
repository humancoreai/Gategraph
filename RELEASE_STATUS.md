# Release Status — GateGraph v0.8.30_STABLE

## Status

Stable release.

## Scope

Operational Stability Gate A-D:

- A: Alert Aggregator
- B: Incident State Manager
- C: Monitoring Export
- D: Minimal deterministic Flood Guard

## Validation

- `operational_stability_evidence`: passed.
- `runaway_cost_evidence`: patched expectation and passed.
- Full Windows CI before patch showed one expected-order mismatch only; all other evidence passed.

## Notes

Flood Guard intentionally runs before session reservation so blocked flood attempts do not create budget side effects.
