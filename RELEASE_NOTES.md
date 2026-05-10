# Release Notes – v0.9.3_STABLE

## Summary

v0.9.3_STABLE is a stable documentation and audit-baseline release. It turns the v0.9.2_STABLE architecture boundary into a referencable governance freeze snapshot.

## Added / preserved

- `docs/GOVERNANCE_FREEZE_SNAPSHOT_v0_9_3.md`
- `docs/INVARIANT_REGISTRY.md`
- `docs/BOUNDARY_REFERENCES.md`
- `docs/RELEASE_REPRODUCIBILITY.md`
- `docs/THREAT_MODEL.md`
- `tests/governance_freeze_evidence.py`

## Stable promotion fix

- Release status metadata now claims `stable`, not `candidate`.
- Release metadata now identifies `v0.9.3_STABLE`.
- Release integrity evidence now targets `v0.9.3_STABLE`.
- Governance freeze snapshot no longer references a missing threat-model file.

## Unchanged

- governance logic
- enforcement logic
- runtime logic
- risk model
- budget model
- agent boundary model

## Release intent

Make the governance baseline reviewable without increasing system capability or autonomy.
