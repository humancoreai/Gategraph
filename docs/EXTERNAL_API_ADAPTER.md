# External API Adapter (v0.8.11)

## Purpose

External API calls are side effects. GateGraph routes them through Enforcement, Session Budget, Runtime Guard, optional Secret Provider, and only then a transport seam.

## Scope

- Evidence tests use deterministic fake/mock transports.
- The adapter no longer accepts caller-supplied `enforcement_allowed` flags.
- Optional `secret_ref_id` allows scoped secret resolution after all guards pass.
- Raw payloads and raw secrets are not logged.

## Pipeline

```text
ExternalAPIRequest
→ Enforcement
→ Session Budget Guard
→ Runtime Guard
→ Secret Provider (optional)
→ Transport
→ Audit Event
```

## Invariants

- No external API execution without valid token.
- Enforcement block prevents Session/Runtime work.
- Session Budget can block expensive API calls.
- Runtime Guard can block repeated API calls.
- Secrets resolve only after all gates pass.
- Missing/out-of-scope secrets block before transport.
- API failures are audited as execution failures, not authorization decisions.
- Untrusted API responses are captured as data, not instructions.

## Evidence

- `tests/external_api_evidence.py`
- `tests/secret_api_integration_evidence.py`
