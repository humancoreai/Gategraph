# Release Notes – v0.16.8_CANDIDATE

Status: candidate  
Base: v0.16.7_STABLE  
Version: 0.16.8
Phase: Release Status Assertion Policy

## Focus

v0.16.8_CANDIDATE introduces evidence profile cleanup and overlap visibility. It does not remove tests, prune gates, or change runtime governance behavior.

## Changes

- Adds an evidence overlap matrix as a descriptive review surface.
- Adds a cleanup evidence gate that proves overlap visibility remains non-authoritative.
- Keeps all existing Evidence CI gates intact for this candidate.

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
