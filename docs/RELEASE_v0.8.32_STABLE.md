# RELEASE v0.8.32_STABLE

## Status

STABLE

## Scope

Single-node usability and read-only monitoring export.

## Summary

This release turns the deterministic GateGraph core into a usable single-node tool without changing Governance, Enforcement, Budget, Runtime, HTTP Policy, Secret Handling or Operational decision logic.

## Added

- Single-node CLI: init, evaluate, status, export-monitoring
- Config loader
- Example config and task files
- Read-only monitoring export

## Validation

Full Windows Evidence CI passed.

## Known limits

- Single-node only
- No server mode
- No distributed budget coordination
- No external monitoring integration
- No automated recovery
