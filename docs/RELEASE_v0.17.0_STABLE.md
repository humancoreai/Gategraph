# GateGraph v0.17.0_STABLE

Release: v0.17.0_STABLE
Base: v0.16.9_STABLE
Status: stable
Version: 0.17.0
Phase: Operational Readiness Baseline

## Scope

This stable release preserves the descriptive Operational Readiness baseline from the validated candidate.

It documents and verifies operational surfaces without changing runtime governance, enforcement logic, policy authority, budget behavior, or semantic governance.

## Invariants

- fail-closed behavior remains unchanged
- no runtime authority is added
- no auto-repair is added
- no auto-promotion is added
- no benchmark/performance claim is made
- Windows CI remains mandatory for stable confirmation

## Evidence

- tests/operational_readiness_evidence.py
- docs/OPERATIONAL_READINESS.md
- registry/operational_readiness_registry.json
