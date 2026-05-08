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

Not yet production-grade:

- token IDs are random DB references, not cryptographically signed tokens
- revocation is checked via DB read per enforcement call
- no concurrency control beyond SQLite constraints
- no role-based human approval model
- no runtime cost/loop governor yet

## Deferred topic

Runaway agent loops and cost control are intentionally out of current scope. They should become a separate Runtime Control Layer later.


## Capability Token Key Management

As of v0.8.9, tokens are signed with an active HMAC key ID and verified against a trusted keyring. This supports bounded rotation in the Single-Node model. It is not yet distributed trust, asymmetric signing, or managed secret storage.
