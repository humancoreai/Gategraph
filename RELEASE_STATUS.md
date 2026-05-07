# Release Status - GateGraph v0.8.10-hygiene-hardening

## Status

Release hygiene hardening on top of v0.8.9.

## Scope

Changed:
- Capability Tokens now include HMAC signature metadata.
- Enforcement verifies token claim integrity before capability use.
- Token DB schema now stores `signature` and `signing_key_id`.
- Reason Normalizer includes token signature/claim mismatch reasons.
- New token-hardening and key-rotation evidence tests added.

Unchanged:
- Governance decision semantics
- Guard Orchestrator order
- Session Budget Guard semantics
- Runtime Guard semantics
- Pattern Engine proposal-only behavior
- External API mock-only scope

## Release note

This release hardens Capability Tokens against simple in-memory mutation and persisted-signature tampering in the current Single-Node model. It prepares the architecture for later stronger token boundaries, but does not yet implement distributed trust or key rotation.


## v0.8.9 addition

Capability Token signing now has explicit key IDs and a trusted keyring. New tokens use the active key; legacy tokens verify only while their key remains trusted. Unknown key IDs fail closed.


## v0.8.10 addition

Closes review findings without changing core behavior: keyring API encapsulation, deterministic single keyring load per enforcement decision, docs/version consistency, schema DDL single-source alignment for Session Budget, explicit transaction precondition, test-only marker, and dev-key warning.
