# PRODUCTION_CHECKLIST.md

## Production criteria for v0.8.34_STABLE

- [x] Deterministic Governance decisions
- [x] Enforcement as only gatekeeper
- [x] No action without Capability Token
- [x] Runtime does not decide
- [x] Fail-closed behavior
- [x] Budget Ledger active
- [x] Cross-session budget enforcement
- [x] Flood Guard active
- [x] Secret isolation
- [x] HTTP policy allowlist
- [x] Append-only audit
- [x] Stable normalized reason codes
- [x] Operational alerting
- [x] Monitoring export
- [x] Single-node CLI init/evaluate/status/export-monitoring
- [x] Server mode uses `src/service_adapter.py`
- [x] Server request validation fail-closed
- [x] Server deterministic JSON error schema
- [x] Server body-size limit
- [x] Server default bind is local (`127.0.0.1`)
- [x] Server public bind warning documented/implemented
- [x] Server `/status` and `/monitoring` remain read-only
- [x] Full Windows Evidence CI passed
- [x] No invariant violations
- [x] No unexpected allows

## Result

GateGraph is production-ready for the defined single-node and local/protected server-adapter scope.

## Out of scope

- Public internet exposure
- Authentication
- TLS
- Reverse proxy setup
- Webhooks
- Background jobs
- Multi-node operation
- External monitoring integration
- Automated recovery
