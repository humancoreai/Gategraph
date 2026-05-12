# Release Notes – v0.15.0_CANDIDATE

Base: v0.14.10_STABLE
Status: candidate
Version: 0.15.0
Phase: Evidence simplification and practical readiness
Release focus: Evidence Simplification / Practical Readiness / Surface Decoupling

## Summary

v0.15.0_CANDIDATE introduces a descriptive evidence registry and begins reducing meta-drift in the Evidence and public-surface layer.

## Changes

- Added `tests/evidence_registry.json` with P0/P1/P2 evidence classification.
- Added `tests/evidence_registry_evidence.py` to validate registry shape and non-authority boundaries.
- Added `docs/EVIDENCE_REGISTRY.md` as the operator-facing explanation surface.
- Declared evidence classification as descriptive only: no pruning, no auto-repair, no policy mutation, no runtime authority.
- Preserved local practical readiness scope from v0.14.10.

## Non-scope

- No new Runtime Authority.
- No Multi-Node.
- No Public Deployment.
- No autonomous policy mutation.
- No auto-repair logic.

## Compatibility Notes

Semantic Registry and Recovery surfaces remain descriptive and non-authoritative.

## Semantic Boundary Confirmation

- No governance logic change.
- No runtime/enforcement behavior change.
- No autonomous policy update.
- No semantic scoring or memory system.
