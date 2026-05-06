# Release Status - GateGraph v0.8.11-secret-api-integration

## Status

Security/architecture hardening on top of v0.8.10.

## Changed

- Added `secret_refs` schema for reference-only secret metadata.
- Added `src/secret_provider.py` with env-backed secret resolution.
- Extended External API request model with optional `secret_ref_id`.
- Added controlled API transport seam.
- Secrets resolve only after Enforcement + Session Budget + Runtime Guard.
- Audit logs secret references and resolution status, never raw secret values.
- Added Secret/API integration evidence tests.

## Unchanged

- Governance decision semantics
- Enforcement token validation semantics
- Guard Orchestrator order
- Runtime/Session Budget semantics
- Pattern Engine proposal-only behavior
- No real network calls in evidence tests

## Release note

This release prepares real API integration without making GateGraph an unrestricted network actor. API execution is still mediated by deterministic guards and scoped secret refs. Production KMS, real HTTP policy, provider plugins, distributed budget, and operational alerting remain future work.
