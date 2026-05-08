# Release Status - GateGraph v0.8.8-capability-token-hardening

## Status

Security hardening release on top of v0.8.7.

## Scope

Changed:
- Capability Tokens now include HMAC signature metadata.
- Enforcement verifies token claim integrity before capability use.
- Token DB schema now stores `signature` and `signing_key_id`.
- Reason Normalizer includes token signature/claim mismatch reasons.
- New token-hardening evidence tests added.

Unchanged:
- Governance decision semantics
- Guard Orchestrator order
- Session Budget Guard semantics
- Runtime Guard semantics
- Pattern Engine proposal-only behavior
- External API mock-only scope

## Release note

This release hardens Capability Tokens against simple in-memory mutation and persisted-signature tampering in the current Single-Node model. It prepares the architecture for later stronger token boundaries, but does not yet implement distributed trust or key rotation.
