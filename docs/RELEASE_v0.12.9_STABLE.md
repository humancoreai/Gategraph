# GateGraph v0.13.3_STABLE

## Phase

Operator Explainability Hygiene.

## Base

`v0.12.8_STABLE`.

## Scope

This stable release carries a small operator-facing explanation surface for fail-closed unknown capability decisions.
It does not change governance logic, enforcement behavior, runtime guards, token semantics, policy mutation rules, or registry authority.

## Changes

- Added `block_reason` to the CLI/service-adapter public decision output for blocked unknown capabilities.
- Added evidence coverage for `RULE-SYNTH-UNKNOWN` operator readability in the single-node CLI.
- Updated the descriptive governance decision surface contract with optional `block_reason`.
- Kept `block_reason` descriptive only; it is not an authorization signal and does not affect decision selection.

## Non-Scope

- No new governance rules.
- No HTTP allowlist expansion.
- No runtime authority.
- No auto-repair, auto-promotion, or semantic scoring.
- No enforcement or token behavior change.

## Evidence

Primary evidence gates:

- `single_node_cli_evidence.py`
- `surface_contract_registry_evidence.py`
- `version_consistency_evidence.py`
- `release_surface_sync_evidence.py`
- `release_integrity_evidence.py`
