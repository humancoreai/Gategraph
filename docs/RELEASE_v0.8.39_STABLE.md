# RELEASE v0.8.39_STABLE

Phase 7: Observability / Explainability.

## Scope

- Added read-only decision trace reconstruction.
- Added explicit guard attribution for runtime guard vs runtime cost guard.
- Added compact explain snapshot.
- Added minimal cost timeline.
- Added observability aggregation for monitoring export.

## Invariants

- No change to core decision logic.
- No mutation from observability functions.
- Trace reconstruction uses persisted runtime evidence only.

## Evidence

- `tests/observability_evidence.py`
- `tests/evidence_ci.py` includes observability evidence.
