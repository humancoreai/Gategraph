Release: v0.17.2_STABLE
Base: v0.17.1_STABLE
Status: stable
Status: stable
Version: 0.17.2
Phase: Promotion Status Drift Guard

# Release Notes – v0.17.2_STABLE

Status: stable  
Base: v0.17.1_STABLE  
Version: 0.17.2
Phase: Promotion Status Drift Guard

## Focus

v0.17.2_STABLE introduces registry schema validation, profile type validation, and release-state normalization. It does not remove tests, prune gates, or change runtime governance behavior.

## Changes

- Adds registry schema validation as descriptive evidence.
- Adds profile type validation and release-state normalization evidence gates.
- Keeps all existing Evidence CI gates intact for this stable release.

## Non-scope

- No automatic evidence pruning.
- No runtime authority changes.
- No governance policy mutation.
- No Multi-Node implementation.


## Runtime / governance boundary

- No governance logic change.
- No runtime/enforcement behavior change.
- No autonomous policy update.
- No semantic scoring or memory system.

## Reviewer-result handling

- README quickstart now separates basic local checks from the full evidence suite.
- `OWASP_AGENTIC_AI_MAPPING.md` is described as a non-normative review mapping.
- Release history remains visible through `CHANGELOG.md`; detailed per-release records remain under `docs/RELEASE_*`.

## Semantic boundary / Registry notes

- Semantic and Registry surfaces remain descriptive, review-only surfaces.
