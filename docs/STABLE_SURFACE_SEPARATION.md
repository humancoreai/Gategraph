# Stable Surface Separation

Release: v0.15.7_CANDIDATE  
Base: v0.15.6_STABLE  
Status: candidate  

This document defines the release-surface cleanup scope for v0.15.7.

## Purpose

v0.15.7 keeps promotion semantics explicit while avoiding accidental confusion between:

- the candidate release token,
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

For the candidate state, public and release surfaces must name `v0.15.7_CANDIDATE` as the current release and `v0.15.6_STABLE` as the base.

The future stable token `v0.15.7_CANDIDATE` may appear only as a future/promotion target, not as the current release.
