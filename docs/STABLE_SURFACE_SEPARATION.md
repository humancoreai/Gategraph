# Stable Surface Separation

Release: v0.17.7_CANDIDATE  
Base: v0.17.7_CANDIDATE  
Status: candidate  

This document defines the release-surface cleanup scope for v0.16.0.

## Purpose

v0.16.0 keeps promotion semantics explicit while avoiding accidental confusion between:

- the stable release token,
- the future stable token,
- the package/root folder name,
- historical release references.

## Boundaries

This is a descriptive release-hygiene layer only.

It does not add:

- runtime authority,
- policy mutation,
- auto-promotion,
- auto-repair,
- new enforcement paths.

## Candidate rule

For the stable state, public and release surfaces must name `v0.17.7_CANDIDATE` as the current release and `v0.17.7_CANDIDATE` as the base.

The future stable token `v0.17.7_CANDIDATE` may appear only as a future/promotion target, not as the current release.
