# GateGraph v0.12.1_STABLE

Base: v0.14.5_STABLE  
Status: candidate  
Phase: Consistency / Recovery Foundation

## Summary

This stable release contains the narrow recovery/replay evidence layer promoted from the tested candidate. It does not change governance, enforcement, runtime authority, token semantics, adapters, deployment mode, or agent behavior.

## Added

- `src/recovery_foundation.py`
- `tests/recovery_foundation_evidence.py`
- `tests/replay_recovery_consistency_evidence.py`
- `tests/surface_recovery_consistency_evidence.py`
- `docs/RECOVERY_FOUNDATION.md`

## Invariant

Recovery checks are descriptive and fail-closed. They do not perform automatic repair, policy mutation, capability recreation, or replay-to-runtime promotion.
