# GateGraph Version

Current: v0.8.12-http-policy-allowlist

## v0.8.12-http-policy-allowlist
- Adds explicit HTTP endpoint policy allowlist for controlled API integrations.
- Real outbound HTTPS-style endpoints require active host/path/method policy before secret resolution and transport execution.
- Local `/mock/` endpoints remain deterministic test seams and do not represent network calls.
- Keeps Enforcement -> Session Budget -> Runtime Guard -> HTTP Policy -> Secret Provider -> Transport ordering.

Previous: v0.8.11-secret-api-integration
