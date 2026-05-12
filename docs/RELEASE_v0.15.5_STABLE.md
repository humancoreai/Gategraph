# GateGraph v0.15.5_STABLE

Base: v0.15.4_STABLE  
Status: stable  
Version: 0.15.5  
Phase: Stable-promotion evidence regression hardening and release-surface consistency cleanup

## Summary

v0.15.5_STABLE hardens the stable-promotion surface evidence after the v0.15.4 Stable test cycle exposed a status-boundary edge case.

## Changes

- Made `stable_promotion_surface_model_evidence` status-sensitive.
- Candidate mode blocks future-Stable current-release claims.
- Stable mode accepts legitimate current-Stable claims after manual promotion.
- Updated the stable-promotion surface model documentation.
- Preserved release, registry, packaging, and evidence checks as descriptive-only surfaces.

## Non-scope

- No runtime logic change.
- No governance mutation.
- No new authority surface.
- No auto-promotion or auto-repair.
