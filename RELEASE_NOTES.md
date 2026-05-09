# Release Notes — GateGraph v0.8.30_CANDIDATE

## Summary

`v0.8.30_CANDIDATE` adds the Operational Stability layer on top of `v0.8.29_STABLE`.

## Added

- Deterministic alert aggregation.
- Manual forward-only incident state transitions.
- Read-only monitoring export object.
- Actor-scoped Flood Guard with hard task/cost window limits.

## Changed

- Guard pipeline now evaluates Flood Guard before session budget reservation.

## Not included

- No autonomous recovery.
- No self-healing.
- No external alert routing.
- No UI.
