# GateGraph v0.17.1_CANDIDATE

Base: v0.17.0_STABLE  
Status: candidate  
Phase: Promotion Status Drift Guard

## Scope

This candidate tightens release-promotion status hygiene after v0.17.0_STABLE exposed residual registry/profile status drift during Stable promotion.

## Changes

- Adds `release_promotion_status_guard_evidence`.
- Adds `registry/release_promotion_status_guard.json`.
- Adds `docs/RELEASE_PROMOTION_STATUS_GUARD.md`.
- Checks that release/profile registries agree with `RELEASE_METADATA.json` for release, base, status, and future-stable tokens.

## Non-scope

No runtime governance behavior changed.
No enforcement, budget, token, HTTP, secret, or policy execution behavior changed.
No automatic promotion or repair authority added.
