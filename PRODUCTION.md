# PRODUCTION.md

GateGraph v0.12.0_STABLE is stable for the defined single-node and local/protected server-adapter scope.

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

## HTTP server exposure boundary

The built-in HTTP server is a local/protected adapter, not an internet-facing production server. It uses Python ThreadingHTTPServer and intentionally does not implement authentication, TLS, rate limiting, connection quotas, reverse-proxy hardening, or distributed DoS protection.

Production rule:

- bind to 127.0.0.1 by default;
- do not expose the server directly to the public internet;
- only place it behind an explicitly controlled boundary if external access is required;
- keep authentication, TLS termination, request throttling, and connection limits outside this adapter until those controls become a dedicated GateGraph scope.

This is not a governance limitation. It is a deployment boundary: the server remains an adapter.


See also `docs/DEPLOYMENT_BOUNDARY.md` for the supported/unsupported/unsafe deployment surface preserved through v0.12.0_STABLE.


See also `docs/STARTUP_SURFACE.md` for canonical local start paths and operational start-surface expectations.


Current release surface: `v0.12.1_STABLE`.


Current release surface: v0.12.7_STABLE.

Current release surface: v0.13.5_STABLE

Release surface: v0.13.6_CANDIDATE.
