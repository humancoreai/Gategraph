# GateGraph v0.13.2_STABLE

Base: v0.13.1_STABLE  
Status: stable
Phase: Candidate CI Gate Hardening

## Scope

v0.13.2_STABLE adds release-gate evidence for the Candidate PASS requirement before Stable promotion. It is a process/integrity hardening release only.

## Added evidence

- tests/candidate_ci_gate_evidence.py

## Invariants

- No governance logic change.
- No runtime logic change.
- No automatic promotion.
- Candidate Windows CI PASS is required before any Stable promotion.
- Release evidence remains descriptive and manual-gated.
