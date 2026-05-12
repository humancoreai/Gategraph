# GateGraph v0.15.6_STABLE

Base: v0.15.5_STABLE  
Status: stable  
Version: 0.15.6  
Phase: CI parity and fresh-clone release-surface consolidation

## Summary

v0.15.6_STABLE consolidates GitHub Actions / Windows CI parity and fresh-clone release-surface validation without changing runtime governance logic.

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
