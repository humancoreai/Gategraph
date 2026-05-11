# GateGraph v0.14.9_CANDIDATE

Base: v0.14.8_STABLE
Status: candidate
Version: 0.14.9
Phase: Release artifact determinism and failure explainability
Release focus: Promotion / Surface / Registry Lock Hardening
Operational release focus: Install / Packaging / Public Repo Hygiene

## Scope

This candidate hardens the release-promotion surface. It does not add runtime authority, auto-promotion, auto-repair, or new governance decision logic.

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

The release pipeline remains descriptive and evidentiary. Stable promotion still requires manual approval and Windows Evidence CI `Passed: True`.
