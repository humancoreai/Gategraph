# Secret Management + Controlled API Integration (v0.8.11)

## Purpose

GateGraph now has a minimal secret-reference layer and a controlled API integration seam.

This is still a Single-Node PoC. It does **not** introduce production KMS, cloud secret managers, distributed trust, or unrestricted network access.

## Model

Secrets are represented as scoped references:

```text
secret_ref_id
→ provider = env
→ secret_name
→ allowed endpoint prefixes
→ allowed capabilities
→ active/disabled
```

Raw secret values are never stored in SQLite. The local provider resolves values from:

- `GATEGRAPH_SECRET_PROVIDER_JSON`, or
- `GATEGRAPH_SECRET_<SECRET_NAME>`

## API path

```text
ExternalAPIRequest
→ Enforcement
→ Session Budget Guard
→ Runtime Guard
→ Secret Provider
→ Transport
→ Audit Event
```

## Invariants

- No API call without valid Capability Token.
- Secrets are resolved only after Enforcement and Guards pass.
- Secret values are passed only to the transport layer.
- Secret values are not logged in audit events.
- Missing/disabled/out-of-scope secrets fail closed.
- Endpoint scope is checked before a secret is released to transport.
- Test transport is deterministic; no real network is used in evidence tests.

## Boundaries

Implemented:

- reference-only secret registry
- env-backed provider
- endpoint/capability scoping
- controlled transport seam
- evidence tests for secret gating and non-logging

Not implemented:

- OS keychain
- cloud KMS / Vault
- secret rotation automation
- real provider plugins
- production HTTP client policy stack
- distributed secret access policy

## Evidence

`tests/secret_api_integration_evidence.py` covers:

- scoped secret reaches transport only after all gates pass
- missing secret blocks before transport
- endpoint scope mismatch blocks before transport
- no-token path blocks before secret resolution
