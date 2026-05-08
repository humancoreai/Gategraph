# GateGraph v0.11.9_STABLE

## Phase

Context / Memory Governance Baseline.

## Summary

v0.11.9_STABLE adds a detection-only delegation boundary model and evidence for multi-agent delegation abuse cases. It does not add new agent powers, runtime modes, adapters, policy mutation, or distributed orchestration.

## Changes

- Added `src/multi_agent_delegation.py`.
- Added `tests/multi_agent_delegation_boundary_evidence.py`.
- Added `docs/MULTI_AGENT_DELEGATION_BOUNDARY.md`.
- Updated release metadata, release notes, manifest inputs, and evidence CI manifest.

## Security posture

Delegation remains observable-only. Transitive authority, circular delegation, capability amplification, unsupported modes, and actor-chain loss fail closed.
