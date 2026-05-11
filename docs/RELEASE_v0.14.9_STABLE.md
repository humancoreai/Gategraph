# GateGraph v0.14.9_STABLE

Base: v0.14.8_STABLE
Status: stable
Version: 0.14.9
Phase: Release artifact determinism and failure explainability
Release focus: Promotion / Surface / Registry Lock Hardening

## Scope

Stable promotion of the v0.14.9 promotion/surface hardening candidate after Windows Evidence CI `Passed: True`.

## Promotion Matrix

Required surfaces:
- RELEASE_METADATA.json
- RELEASE_MANIFEST.json
- RELEASE_STATUS.md
- RELEASE_NOTES.md
- VERSION.md
- README.md
- pyproject.toml
- tools/build_release.py
- tools/verify_release.py
- registry/semantic_registry_lock.json
- registry/promotion_pipeline_registry.json
- tests/promotion_surface_matrix_evidence.py
- tests/promotion_status_ssot_evidence.py

## Non-authority statement

The release pipeline remains descriptive and evidentiary. Stable promotion does not add runtime authority, auto-promotion, auto-repair, or policy mutation.

Operational release focus: Install / Packaging / Public Repo Hygiene
