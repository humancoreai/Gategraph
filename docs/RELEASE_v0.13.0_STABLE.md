# GateGraph v0.13.0_STABLE

Base: v0.12.9_STABLE

Status: stable

Phase: Release Consistency Hardening.

## Scope

This stable release carries a deterministic release-claim consistency evidence layer. The goal is to reduce drift between release metadata, release notes, README/status surfaces, changelog and the release document.

## Invariants

- Governance logic unchanged.
- Runtime logic unchanged.
- Enforcement logic unchanged.
- No automatic promotion or repair.
- Evidence remains descriptive-only.
- Stable promotion requires external Windows CI confirmation.

## Evidence

- `release_claim_consistency_evidence.py`
- Existing release, surface, registry, semantic and recovery evidence gates remain active.

## Non-scope

- No production deployment change.
- No distributed governance.
- No semantic scoring.
- No policy-learning or autonomous mutation.
