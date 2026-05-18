# Evidence Suite Profile Management

Status: descriptive release evidence.
Release: v0.17.2_CANDIDATE.
Base: v0.14.7_STABLE.

## Purpose

GateGraph now has a broad evidence suite. That is intentional, but unmanaged breadth creates noise, runtime cost, and duplicate failures. This document defines evidence profiles without deleting tests or weakening release gates.

## Profiles

- `core`: fast governance, runtime, enforcement, and security invariants.
- `release`: version, manifest, packaging, registry lock, Candidate/Stable transition, and surface consistency checks.
- `extended`: replay, archive, operator, drift, semantic, monitoring, and scenario evidence.

## Rules

- Profiles are descriptive grouping only.
- A profile cannot disable a mandatory gate.
- Stable promotion still requires full Windows CI `Passed: True`.
- No automatic pruning, no auto-repair, no governance mutation.
- Redundant tests may later be consolidated only by explicit human decision.

## Non-scope

This release does not remove tests and does not introduce a faster CI runner mode as release authority.
