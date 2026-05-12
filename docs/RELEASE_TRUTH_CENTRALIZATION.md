# Release Truth Centralization

Release: v0.15.3_CANDIDATE  
Base: v0.15.2_STABLE  
Status: candidate  

v0.15.3 introduces a small read-only release truth resolver.

## Purpose

The release, base, status, version, phase, and focus values are derived from `RELEASE_METADATA.json` instead of being repeatedly interpreted by every release/evidence surface.

## Boundary

This is release-evidence plumbing only.

It does not add:

- runtime authority,
- governance authority,
- policy mutation,
- auto-promotion,
- auto-repair,
- new enforcement behavior.

## Candidate rule

Candidate surfaces must name `v0.15.3_CANDIDATE` as the current release and `v0.15.2_STABLE` as the base.

`v0.15.3_STABLE` is only a future promotion target and must not appear as the current public release while metadata status is `candidate`.
