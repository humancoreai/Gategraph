# GateGraph v0.17.0_CANDIDATE

Release: v0.17.0_CANDIDATE
Base: v0.16.9_STABLE
Status: candidate
Version: 0.17.0
Phase: Operational Readiness Baseline

## Scope

This candidate adds a descriptive Operational Readiness baseline.

It documents and verifies operational surfaces without changing runtime governance, enforcement logic, policy authority, budget behavior, or semantic governance.

## Invariants

- fail-closed behavior remains unchanged
- no runtime authority is added
- no auto-repair is added
- no auto-promotion is added
- no benchmark/performance claim is made
- Windows CI remains mandatory before stable promotion

## Evidence

- tests/operational_readiness_evidence.py
- docs/OPERATIONAL_READINESS.md
- registry/operational_readiness_registry.json
