# Known Gaps Roadmap – v0.10.0_CANDIDATE

## Closed before / at v0.9.3

- LICENSE present
- CHANGELOG present
- CONTRIBUTING present
- RELEASE_MANIFEST populated
- Caller-boundary metadata required at service adapter boundary
- Governance freeze snapshot and invariant registry present
- Missing `docs/THREAT_MODEL.md` reference fixed in v0.9.3_STABLE_FIXED

## Closed / hardened in v0.10.0_CANDIDATE

- Naked `governance.evaluate_task()` invocation fails closed by default unless a trusted entry context is supplied.
- Service adapter supplies the trusted production entry context after caller-boundary validation.
- Runtime boundary hardening evidence verifies direct default denial and adapter-mediated success.

## Still open – product/deployment

- HTTP adapter has no built-in Auth/TLS; reverse-proxy/auth reference architecture remains future work.
- No KMS-backed secret management.
- Capability-token signing remains symmetric HMAC.
- SQLite remains single-node storage.
- No pip package / `pyproject.toml` packaging baseline.
- No Docker/Systemd deployment baseline.
- No external framework integration examples.
- No UI/dashboard.
- No operator alert routing integration.
- No audit-log retention management.
- No security-disclosure process.

## Non-scope for v0.10.0

- no new agents
- no new adapters
- no distributed governance
- no new runtime execution model
- no product UI

## v0.10.1 update – Runtime / Boundary Hardening

Closed / improved:
- Direct Governance entry is fail-closed without trusted entry context.
- Public evaluation entry is explicitly classified as `service_adapter`.
- Forbidden caller classes now fail closed in runtime evidence.
- Selected freeze assumptions are covered by executable runtime invariant evidence.

Still open:
- Auth/TLS reference architecture.
- Asymmetric token signing / KMS.
- Packaging and deployment baseline.
- Real external framework integration.



## v0.11.0_STABLE – Runtime Chain/Order Assertions

Closed / hardened:
- guard-chain order is now executable via `src/runtime_chain_assertions.py`
- skipped-stage detection is covered by evidence
- invalid downstream execution after Enforcement denial fails closed
- freeze-aware runtime invariant evidence now covers chain/order behavior

Still open:
- no Auth/TLS deployment boundary
- no asymmetric token signing
- no KMS
- no packaging/deployment baseline
- no external framework integration
