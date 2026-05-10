# Release Notes — GateGraph v0.11.9_STABLE

Base: `v0.11.8_STABLE`
Status: stable

## Summary

`v0.11.9_STABLE` is a governance semantics stabilization release. It tightens the distinction between runtime objects and reference objects and cleans the repository root surface.

## Added

- `docs/GOVERNANCE_SEMANTICS_MODEL.md`
- `docs/ROOT_SURFACE.md`
- `tests/governance_semantics_evidence.py`
- `tests/root_surface_hygiene_evidence.py`
- `tests/version_consistency_evidence.py`

## Changed

- Release metadata, version surfaces, packaging tools, and evidence expectations updated to `v0.11.9_STABLE`.
- Development/release-history artifacts moved from repository root to `docs/release_artifacts/`.

## Non-goals

No memory system, vector database, semantic scoring, autonomous context filtering, runtime authority expansion, or new governance capability is introduced.
