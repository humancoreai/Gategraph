# GateGraph v0.12.4_STABLE

Base: v0.14.5_STABLE  
Status: stable  
Phase: Recovery & Replay Hardening

## Purpose

This stable release hardens recovery and replay consistency around idempotency, collision handling, deterministic replay order, reference integrity, and release/surface synchronization.

## Scope

- descriptive recovery idempotency
- duplicate recovery attempt visibility
- reservation recovery collision blocking
- partial-state fail-closed recovery classification
- deterministic replay ordering
- replay/explain/archive/recovery reference integrity
- manifest, registry, freeze and release surface synchronization

## Non-scope

- no governance logic change
- no enforcement logic change
- no runtime authority expansion
- no automatic repair or self-healing
- no replay execution
- no policy learning
- no external dependencies

## Evidence

- `tests/recovery_idempotency_evidence.py`
- `tests/replay_order_determinism_evidence.py`
- `tests/recovery_surface_registry_evidence.py`
- `tests/release_surface_sync_evidence.py`
- `tests/replay_reference_integrity_evidence.py`
- full `tests/evidence_ci.py`
