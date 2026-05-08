# GateGraph v0.11.9_STABLE

Phase: Context / Memory Governance Baseline

## Scope

v0.11.9_STABLE adds explicit security mapping documentation and strengthens reviewer-facing exposure boundaries for token, Authorization header, and secret material.

## Added

- `SECURITY_MODEL.md`
- `OWASP_AGENTIC_AI_MAPPING.md`
- `KNOWN_LIMITATIONS.md`
- `src/security/token_redaction.py`
- `tests/token_exposure_evidence.py`

## Invariants

- No governance rule change.
- No enforcement authority expansion.
- No runtime mode expansion.
- No new agentic behavior.
- No distributed/cloud/runtime sandbox claim.
- Raw tokens, bearer payloads, signatures, signing input, and secret values remain excluded from audit/explain/monitoring views.

## Evidence

- `tests/token_exposure_evidence.py`
- Existing Evidence CI remains the release gate.
