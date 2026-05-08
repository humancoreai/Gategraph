# GateGraph Version

Current: v0.8.5-api-enforcement-binding

Previous: v0.8.4-external-api-mock-adapter

Notes:
- External API Adapter now invokes Enforcement internally.
- Callers can no longer pass a spoofable enforcement_allowed boolean.
- Mock-only API behavior remains unchanged.
- External API Evidence updated to use real capability tokens or None.

Versioning hygiene:
- Product/release version: `v0.8.5-api-enforcement-binding`.
- Audit `schema_version` remains `0.8.3` intentionally because v0.8.4/v0.8.5 did not change the event schema.
- `actor_version` is `0.8.5` for newly written events so evidence can distinguish the current implementation from the stable audit schema.
- CI/evidence runner uses `python -S -u` to avoid environment-level site-package shutdown/import side effects and to keep test execution deterministic.


## v0.8.6-runaway-cost-control

Security hardening release. Runtime and Session Budget guards now reject non-positive cost values fail-closed. Schema version remains 0.8.3 because no audit table shape changed.
