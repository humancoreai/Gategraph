# GateGraph Version

Current: v0.8.11-secret-api-integration

Previous: v0.8.10-hygiene-hardening

## v0.8.11-secret-api-integration

Security/architecture release. Adds reference-only secret management and a controlled API transport seam. Secrets are resolved only after Enforcement, Session Budget, and Runtime Guard pass. Raw secret values are not persisted or logged. Evidence tests cover secret resolution, missing secrets, endpoint scope mismatch, and no-token blocking before secret resolution.

Still not production-grade: no KMS/OS keychain, no real HTTP policy stack, no distributed trust, no automated secret rotation.

## v0.8.10-hygiene-hardening

Release hygiene hardening. No governance semantics changed. Fixes: public keyring API, single keyring load per enforcement decision, SECURITY.md/version drift, Session Budget DDL single-source alignment, explicit transaction precondition documentation, test-only expired token marker, and development-key warning.

## v0.8.9-token-key-management

Capability Token signing supports explicit active key IDs and trusted keyrings for bounded HMAC key rotation. Unknown signing keys fail closed. No distributed trust or asymmetric signing yet.

## v0.8.8-capability-token-hardening

Capability Tokens carry HMAC signatures over immutable claims and Enforcement validates persisted claims plus signature before granting capabilities. Audit schema version remains `0.8.3`; token storage schema is extended with token-level signature metadata.
