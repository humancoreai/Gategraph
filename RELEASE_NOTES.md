# Release Notes – v0.11.4_STABLE

Status: stable
Base: v0.11.3_STABLE
Phase: Capability Token Audit Redaction

v0.11.4_STABLE adds a narrow security hardening layer for capability-token audit references. Audit events may correlate token issuance and enforcement through `token_id` and `token_hash`, but must not persist raw token objects, HMAC signatures, signing input, Authorization headers, bearer values, or signing secret material.

Added:
- `docs/CAPABILITY_TOKEN_AUDIT_REDACTION.md`
- `tests/capability_token_redaction_evidence.py`
- audit-safe token reference helpers for `token_id` and `token_hash`
- redacted `capability_token_issued` and `enforcement_allowed` audit events

No Governance decision model, Runtime Guard behavior, Enforcement rule, budget policy, secret resolution, HTTP policy, adapter authority, agentic behavior, distributed governance, cloud/Docker/Kubernetes layer, or UI behavior is introduced.
