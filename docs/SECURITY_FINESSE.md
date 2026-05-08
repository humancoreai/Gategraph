# Security Finesse (v0.8.13)

Block B focuses on edge-case confidence, not new capability.

## Checks

- Secret values may reach the transport seam, but must not appear in audit/evidence.
- HTTP Policy denial happens before Secret Provider resolution.
- Parent hosts do not implicitly allow subdomains.
- Wildcard host policies are rejected explicitly.
- Path-prefix matching is boundary-aware: `/v1` allows `/v1` and `/v1/...`, not `/v10` or `/v1evil`.
- HTTP method matching is normalized to uppercase.
- Combined expired and revoked token states remain fail-closed with deterministic expiry-first rejection.

## Invariant

No external side effect may happen before this sequence succeeds:

`Enforcement -> Session Budget -> Runtime Guard -> HTTP Policy -> Secret Provider -> Transport`

## Scope Limit

This is still a Single-Node PoC. It does not add KMS, OS keychain, real HTTP client behavior, distributed trust, or production incident handling.
