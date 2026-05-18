# GateGraph v0.8.34_STABLE – Server Hardening / Safe Service Boundary

## Status

Candidate only. No stable promotion without Full Windows Evidence CI.

## Scope

Phase 3 hardens the existing server mode while preserving the adapter boundary:

- deterministic JSON error schema for server failures
- fail-closed request validation for `/evaluate`
- bounded request bodies
- explicit JSON content-type requirement
- JSON errors for unsupported methods and unknown endpoints
- safe bind default remains `127.0.0.1`
- public bind emits an operator warning
- `/status` and `/monitoring` remain read-only observation endpoints

## Invariants

- Server does not make governance decisions.
- Server calls `src/service_adapter.py` for evaluation, status and monitoring.
- CLI behavior is not changed.
- No authentication, TLS, reverse proxy, webhooks, background jobs or multi-node behavior added in this phase.

## Evidence

Added:

- `tests/server_hardening_evidence.py`

Updated aggregate manifest:

- `tests/evidence_ci.py`

Focused local evidence executed in this package:

```text
PASS server_mode_evidence
PASS server_hardening_evidence
```

Full aggregate CI was not completed in this Linux container because the existing aggregate runner hung during `evidence_runner_selftest`. This is not a stable release claim.
