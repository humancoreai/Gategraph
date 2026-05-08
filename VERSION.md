# GateGraph Version

Current: v0.8.5-api-enforcement-binding

Previous: v0.8.4-external-api-mock-adapter

Notes:
- External API Adapter now invokes Enforcement internally.
- Callers can no longer pass a spoofable enforcement_allowed boolean.
- Mock-only API behavior remains unchanged.
- External API Evidence updated to use real capability tokens or None.
