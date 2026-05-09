# Release Notes — GateGraph v0.12.2_CANDIDATE

## v0.12.2_CANDIDATE — Recovery & Replay Hardening

Base: v0.12.1_STABLE  
Status: candidate

### Added
- Recovery idempotency helpers for duplicate recovery attempts and partial-state recovery classification.
- Reservation recovery collision hardening for conflicting reservation state and event-derived finality.
- Deterministic replay ordering using explicit sequence fields before descriptive fallback fields.
- Reference-integrity checks ensuring replay/explain/archive/recovery objects remain non-executable and non-authoritative.
- Release/surface registry synchronization evidence for recovery, replay, freeze, manifest, metadata and CI surfaces.

### Evidence gates
- `recovery_idempotency_evidence`
- `replay_order_determinism_evidence`
- `recovery_surface_registry_evidence`
- `release_surface_sync_evidence`
- `replay_reference_integrity_evidence`

### Boundary invariants
- No governance logic change.
- No runtime/enforcement behavior change.
- No autonomous policy update.
- No semantic scoring or memory system.

### Non-scope
- No automatic repair loop.
- No policy mutation.
- No new runtime authority.
- No replay execution or runtime rehydration.
- No distributed recovery protocol.
- No external dependency.

## Evidence expectation

Run:

```powershell
python tests\evidence_ci.py
```
