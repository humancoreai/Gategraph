# GateGraph v0.14.8_CANDIDATE
Phase: Release artifact determinism and failure explainability

Status: candidate  
Base: v0.14.7_STABLE

## Scope

v0.14.8_CANDIDATE hardens release/evidence determinism without adding governance logic or runtime authority.

## Changes

- Adds descriptive root-cause grouping evidence for related CI failures.
- Adds artifact determinism evidence for manifest order and generated-artifact exclusion.
- Adds fresh-clone surface validation evidence for clean-checkout reproducibility.
- Keeps governance proposal-only and enforcement boundaries unchanged.

## Non-scope

- No autonomous policy mutation.
- No runtime authority expansion.
- No adaptive or ML-based decisions.
- No Stable promotion before Windows Candidate CI PASS.
