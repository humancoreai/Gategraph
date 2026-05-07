# GateGraph Version

Current: v0.8.10-hygiene-hardening

Previous: v0.8.9-token-key-management

Notes:
- External API Adapter now invokes Enforcement internally.
- Callers can no longer pass a spoofable enforcement_allowed boolean.
- Mock-only API behavior remains unchanged.
- External API Evidence updated to use real capability tokens or None.

Versioning hygiene:
- Product/release version: `v0.8.5-api-enforcement-binding`.
- Audit `schema_version` remains `0.8.3` intentionally because v0.8.4/v0.8.5 did not change the event schema.
- `actor_version` is `0.8.5` for newly written events so evidence can distinguish the current implementation from the stable audit schema.
- CI/evidence runner uses `python -S -u` to avoid environment-level site-package shutdown/import side effects and to keep test execution deterministic.


## v0.8.6-runaway-cost-control

Security hardening release. Runtime and Session Budget guards now reject non-positive cost values fail-closed. Schema version remains 0.8.3 because no audit table shape changed.

## v0.8.7-ci-runner-stabilization

Release hygiene stabilization. Evidence execution was moved toward bounded runner behavior. Production governance/enforcement/runtime semantics unchanged.

## v0.8.8-capability-token-hardening

Security hardening release. Capability Tokens now carry HMAC signatures over immutable claims and Enforcement validates persisted claims plus signature before granting capabilities. Audit schema version remains `0.8.3`; token storage schema is extended with token-level signature metadata.


## v0.8.9-token-key-management

Security hardening release. Capability Token signing now supports explicit active key IDs and trusted keyrings for bounded HMAC key rotation. Unknown signing keys fail closed. No distributed trust or asymmetric signing yet.


## v0.8.10-hygiene-hardening

Release hygiene hardening. No governance semantics changed. Fixes: public keyring API, single keyring load per enforcement decision, SECURITY.md/version drift, Session Budget DDL single-source alignment, explicit transaction precondition documentation, test-only expired token marker, and development-key warning.
