# RELEASE v0.8.34_STABLE

## Title

Server Hardening / Safe Service Boundary

## Status

Stable. Promoted from `v0.8.34_CANDIDATE` after Full Windows Evidence CI passed.

## Promotion basis

Observed Windows evidence run:

```text
PS C:\users\user\desktop\gategraph\GateGraph_v0.8.34_CANDIDATE> python tests\evidence_ci.py
...
--- server_hardening_evidence ---
PASS server_hardening_evidence
Summary: {'passed': 1, 'failed': 0}
...
CI EVIDENCE REPORT
Log: C:\Users\User\Desktop\Gategraph\GateGraph_v0.8.34_CANDIDATE\tests\logs\ci_evidence_20260429_052441.json
Passed: True
```

## Scope

v0.8.34_STABLE hardens server mode while preserving the adapter boundary.

Included:

- deterministic JSON error schema for server-boundary failures
- fail-closed request validation for `/evaluate`
- bounded request bodies
- explicit JSON content-type requirement
- JSON errors for unsupported methods and unknown endpoints
- safe bind default `127.0.0.1`
- explicit warning for public bind (`0.0.0.0` / `::`)
- read-only assurance for `/status` and `/monitoring`

## Invariants

- Server does not make governance decisions.
- Server calls `src/service_adapter.py` for evaluate/status/monitoring.
- CLI behavior remains unchanged.
- No authentication, TLS, reverse proxy, webhooks, background jobs or multi-node behavior added.
- No new autonomy introduced.
- Monitoring state is not mutated by observation endpoints.

## Evidence files

- `tests/server_mode_evidence.py`
- `tests/server_hardening_evidence.py`
- `tests/evidence_ci.py`

## Result

v0.8.34_CANDIDATE is promoted to **v0.8.34_STABLE** for the defined local/protected server-adapter scope.
