# External API Mock Adapter (v0.8.4)

## Purpose

External API calls are side effects. GateGraph v0.8.4 introduces a controlled mock adapter to prove outbound calls only occur after the full guard pipeline.

## Scope

- Mock only.
- No real network calls.
- No secrets.
- No raw payload logging.
- Deterministic responses for testing.

## Pipeline

```text
ExternalAPIRequest
→ Guard Orchestrator
→ Enforcement result
→ Session Budget Guard
→ Runtime Guard
→ Mock API execution
→ Audit Event
```

## Mock behaviors

- `success`
- `timeout`
- `rate_limit`
- `server_error`
- `untrusted_response`

## Invariants

- No external call without guard pipeline.
- Enforcement block prevents Session/Runtime work.
- Session Budget can block expensive API calls.
- Runtime Guard can block repeated API calls.
- API failures are audited as execution failures, not authorization decisions.
- Untrusted API responses are captured as data, not instructions.

## Evidence

`tests/external_api_evidence.py` proves:

- allowed mock call completes
- no-token call blocks before API
- session budget blocks expensive API
- runtime budget blocks repeated API
- timeout is audited
- rate limit is audited
- untrusted response stays data-only
