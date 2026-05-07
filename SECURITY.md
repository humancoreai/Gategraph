# Security Notes

## Core security model

GateGraph follows fail-closed governance.

Security-critical invariants:

- no action without token
- no expired token
- no revoked token
- no cross-task token reuse
- no capability not explicitly granted
- no automatic allow for critical risk
- no direct execution of agent output

## Current PoC limitations

This PoC is intentionally local and minimal.

Implemented at PoC level:

- HMAC-signed capability tokens with explicit signing key IDs
- trusted keyring verification for bounded local key rotation
- DB-backed revocation checks per enforcement call
- Runtime Guard for per-task loops/steps/cost
- Session Budget Guard for global and agent-level cost limits

Not yet production-grade:

- no managed KMS/OS-keychain integration; only env-backed reference secrets at PoC level
- no asymmetric signatures or distributed trust boundary
- no multi-node/distributed budget coordination
- no role-based human approval model
- no unrestricted real external API execution; controlled transport seam only

## Deferred production topics

Runaway agent loops and cost control are covered at PoC level by Runtime Guard and Session Budget Guard. Remaining work is production hardening: real billing integration, distributed budget state, and operational alerting.


## Capability Token Key Management

As of v0.8.9, tokens are signed with an active HMAC key ID and verified against a trusted keyring. This supports bounded rotation in the Single-Node model. It is not yet distributed trust, asymmetric signing, or managed secret storage.

## Secret Management PoC

As of v0.8.11, GateGraph supports scoped secret references for API integrations. Raw values are not stored in SQLite and are resolved only after Enforcement and Guards pass. The current provider is env-backed and intended for local PoC/evidence use, not production secret management. Missing, disabled, or out-of-scope secrets fail closed.
