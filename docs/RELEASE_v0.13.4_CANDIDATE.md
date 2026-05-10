# GateGraph v0.13.4_CANDIDATE Release

Status: candidate.
Base: v0.13.3_STABLE.

## Scope

Evidence Failure Classification.

This candidate adds descriptive classification for evidence failures so CI failures can be grouped as release-surface, semantic-boundary, registry-lock, server-hardening, or runtime-governance issues without changing runtime behavior.

## Invariants

- Descriptive classification only.
- No automatic repair.
- No automatic pruning.
- No Stable promotion without Candidate Windows CI `Passed: True`.
- No governance, runtime, or enforcement logic change.
