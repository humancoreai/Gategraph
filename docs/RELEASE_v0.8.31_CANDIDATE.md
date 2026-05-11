# RELEASE v0.8.31_STABLE

## Scope

Single-node usability layer.

## Added

- `src/cli.py` as single-node CLI adapter
- `src/config_loader.py` for dependency-free YAML/JSON configuration loading
- `config.example.yaml`
- `task.example.json`
- `tests/single_node_cli_evidence.py`

## Invariants

- No governance logic was duplicated or bypassed.
- CLI initializes and uses the existing database, rule, session-budget and runtime-budget paths.
- Unsupported runtime modes fail closed.
- Server mode is intentionally not enabled in this version.

## Evidence

- `single_node_cli_evidence`: passed

## Status

Candidate. Stable promotion requires full CI evidence on Windows.
