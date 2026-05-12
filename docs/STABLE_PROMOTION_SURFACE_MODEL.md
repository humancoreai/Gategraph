# Stable Promotion Surface Model

Release: `v0.15.4_STABLE`  
Base: `v0.15.4_STABLE`  
Status: `candidate`

This document defines the descriptive release-surface model used before a Candidate is manually promoted to Stable.

## Purpose

The model separates two states that must not be mixed:

- Candidate verification surfaces: current working truth for CI and review.
- Future Stable promotion surfaces: manually produced after Candidate CI has passed.

## Invariants

- The model is descriptive only.
- It grants no runtime authority.
- It does not auto-promote Candidate artifacts.
- It does not auto-repair release metadata.
- It does not mutate governance policy.

## Candidate surface rule

For `v0.15.4_STABLE`, public release surfaces must continue to name `v0.15.4_STABLE` until a dedicated Stable package is created.

## Stable surface rule

A future Stable package may differ only in explicit promotion fields:

- release token
- status
- release document path
- ZIP name
- root folder
- manifest kind

All governance, runtime, registry, evidence and security invariants remain unchanged.
