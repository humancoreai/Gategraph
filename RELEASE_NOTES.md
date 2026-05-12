# Release Notes – v0.15.5_STABLE

Base: v0.15.4_STABLE  
Status: stable  
Version: 0.15.5  
Phase: Stable-promotion evidence regression hardening and release-surface consistency cleanup  
Release focus: Stable Promotion Evidence Regression Hardening / Release Surface Consistency

## Summary

v0.15.5_STABLE is a narrow consolidation release. It hardens the stable-promotion surface model after the v0.15.4 Stable test cycle exposed that legitimate Stable claims could still be interpreted as Candidate-only violations.

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

v0.15.5_STABLE is based on v0.15.4_STABLE and keeps the single-node local protected deployment boundary unchanged.

## Semantic Boundary Confirmation

- No governance logic change.
- No runtime/enforcement behavior change.
- No autonomous policy update.
- No semantic scoring or memory system.
- Semantic Registry and Recovery surfaces remain descriptive and non-authoritative.
