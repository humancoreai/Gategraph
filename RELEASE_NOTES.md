Release: v0.17.0_STABLE
Base: v0.16.9_STABLE
Status: stable
Version: 0.17.0
Phase: Operational Readiness Baseline

# Release Notes – v0.17.0_STABLE

Status: stable  
Base: v0.16.9_STABLE  
Version: 0.17.0
Phase: Operational Readiness Baseline

## Focus

v0.17.0_STABLE introduces evidence profile cleanup and overlap visibility. It does not remove tests, prune gates, or change runtime governance behavior.

## Changes

- Adds an evidence overlap matrix as a descriptive review surface.
- Adds a cleanup evidence gate that proves overlap visibility remains non-authoritative.
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
