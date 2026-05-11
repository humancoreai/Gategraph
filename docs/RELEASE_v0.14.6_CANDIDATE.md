# GateGraph v0.14.6_CANDIDATE

Status: candidate  
Base: v0.14.5_STABLE  
Release: v0.14.6_CANDIDATE
Phase: Install / Packaging / Public Repo Hygiene

## Scope

v0.14.6 hardens the release promotion pipeline without changing runtime governance behavior.

## Focus

- Promotion pipeline consistency checks.
- Manifest and registry-lock rebuild visibility.
- Candidate-to-stable surface expectations.
- Early release-surface drift detection.

## Invariants

- No runtime authority expansion.
- No automatic promotion.
- No automatic policy mutation.
- Evidence remains descriptive and deterministic.
- Stable promotion still requires a passing Windows CI run on this candidate.

## Notes

This release exists to prevent the class of v0.14.5 promotion drift where stable surfaces, candidate transition evidence, manifest entries, and registry locks could become temporarily inconsistent.
