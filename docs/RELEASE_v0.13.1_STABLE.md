# GateGraph v0.13.3_STABLE

Base: v0.14.7_STABLE  
Status: stable  
Scope: Recovery Replay Finality Hardening.

## Summary

v0.13.3_STABLE adds evidence-only hardening for recovery/replay finality. It verifies that final recovery states remain final, conflicting finality fails closed, and recovery snapshots stay reference-only.

## Added

- `tests/recovery_replay_finality_evidence.py`
- `docs/RECOVERY_REPLAY_FINALITY.md`
- `recovery_replay_finality_scope` metadata marker

## Non-scope

- no governance logic change;
- no runtime/enforcement logic change;
- no autonomous repair;
- no replay-to-runtime rehydration;
- no policy mutation;
- no new authority surface.

## Validation

Stable release requires full Windows Evidence CI before stable promotion.
