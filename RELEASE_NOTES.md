# Release Notes – v0.11.5_CANDIDATE

## Summary

v0.11.5_CANDIDATE is a security boundary hardening release. It makes GateGraph's security posture more reviewable and adds explicit evidence that token, Authorization header, base64 token, and secret material do not leak through audit, explain, or monitoring surfaces.

## Added

- `SECURITY_MODEL.md`
- `OWASP_AGENTIC_AI_MAPPING.md`
- `KNOWN_LIMITATIONS.md`
- `docs/RELEASE_v0.11.5_CANDIDATE.md`
- `src/security/token_redaction.py`
- `tests/token_exposure_evidence.py`

## Changed

- Audit event logging now applies centralized sensitive-field redaction before persistence.
- Monitoring export now applies sensitive-field redaction before returning reviewer-facing data.
- Capability token audit references expose `token_id`, `token_hash`, and key identifiers, not signatures or raw token material.

## Not changed

- No governance rule change.
- No enforcement authority change.
- No runtime surface expansion.
- No adapter authority expansion.
- No distributed/cloud/runtime sandbox claim.
