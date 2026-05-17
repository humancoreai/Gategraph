# Release Status Token Centralization

Release: v0.16.7_STABLE  
Base: v0.16.6_STABLE  
Status: stable

This surface documents a descriptive-only cleanup for release/status tokens. It does not add runtime authority, auto-promotion, policy mutation, or governance repair behavior.

## Purpose

Previous Candidate/Stable rounds exposed repeated drift from hardcoded status assumptions in evidence gates. This phase makes the expected token relationship explicit:

- `release` is the current release token.
- `base` is the previous stable baseline.
- `status` must match the release suffix.
- `future_stable` is derived from status, not copied blindly.

For a candidate release, `future_stable` must be the same version with `_STABLE`. For a stable release, `future_stable` must equal the current release.

## Boundaries

- Descriptive evidence only.
- No runtime authority.
- No automatic repair.
- No automatic promotion.
- No governance logic change.
