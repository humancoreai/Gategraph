# Capability Token Audit Redaction

Release: `v0.11.4_STABLE`

Capability tokens are authorization material. Audit records may prove which token was involved in issuance or enforcement, but they must not store the raw token object, token signature, signing input, Authorization header, bearer value, or signing secret material.

Allowed audit fields:

- `token_id`
- `token_hash`
- `key_id`
- `task_id`
- `decision_id`
- `expires_at`
- budget constraint references

`token_hash` is a deterministic SHA-256 fingerprint for correlation. It is not a replacement token and cannot be replayed as authorization material.

Forbidden audit fields:

- raw capability token objects
- HMAC signatures
- signing input
- signing secrets
- Authorization headers
- bearer values

Scope boundary: this release does not change Governance decisions, Runtime Guard behavior, Enforcement rules, budget policy, secret resolution, HTTP policy, deployment mode, or multi-agent behavior.
