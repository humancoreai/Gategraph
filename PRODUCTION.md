# PRODUCTION.md

GateGraph v0.8.34_STABLE is production-ready for the defined single-node and local/protected server-adapter scope.

## Scope

- Single-node operation
- CLI evaluation
- Local/protected HTTP server adapter
- `POST /evaluate` via the shared `src/service_adapter.py` path
- `GET /status` and `GET /monitoring` as read-only observation endpoints
- Deterministic governance and enforcement
- Runtime/session/flood/budget guards
- Read-only monitoring export
- Deterministic server-boundary error schema

## Out of scope

- Public internet exposure
- Authentication
- TLS
- Reverse proxy configuration
- Webhooks
- Background jobs
- Multi-node operation
- Distributed budget coordination
- External monitoring integration
- Automated recovery

## Responsibility model

- Human: final decision authority
- Governance: rule enforcement
- Runtime: execution only
- Operational layer: read-only observation
- CLI/Server adapters: no independent decision logic

## Stable basis

Stable promotion is based on a passed Full Windows Evidence CI run for v0.8.34, including the new server hardening evidence.
