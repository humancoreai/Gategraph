# Release Notes – v0.15.6_CANDIDATE

Base: v0.15.5_STABLE  
Status: candidate  
Version: 0.15.6  
Phase: CI parity and fresh-clone release-surface consolidation  
Release focus: CI Parity / Fresh Clone Release Surface Consolidation

## Summary

v0.15.6_CANDIDATE is a narrow consolidation Candidate focused on GitHub Actions / Windows CI parity, fresh-clone reproducibility, release-surface drift prevention, and deterministic packaging hygiene.

## Changes

- Updated `tests/stable_promotion_surface_model_evidence.py` to evaluate Candidate and Stable states separately.
- Candidate state still blocks future-Stable current-release claims.
- Stable state accepts current-Stable claims as legitimate release truth after manual promotion.
- Updated `registry/stable_promotion_surface_model.json` and `docs/STABLE_PROMOTION_SURFACE_MODEL.md` to document the status-sensitive rule.
- Preserved descriptive-only boundaries: no runtime authority, no auto-promotion, no auto-repair, no policy mutation.

## Non-scope

- No governance logic change.
- No Runtime Layer change.
- No Enforcement Layer change.
- No new feature scope.

## Compatibility Notes

v0.15.6_CANDIDATE is based on v0.15.5_STABLE and keeps the single-node local protected deployment boundary unchanged.

## Semantic Boundary Confirmation

- No governance logic change.
- No runtime/enforcement behavior change.
- No autonomous policy update.
- No semantic scoring or memory system.
- Semantic Registry and Recovery surfaces remain descriptive and non-authoritative.
