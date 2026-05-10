# Known Gaps Roadmap – v0.12.4_STABLE
Current release context: v0.12.4_STABLE.


## Closed before / at v0.9.3

- LICENSE present.
- CHANGELOG present.
- CONTRIBUTING present.
- RELEASE_MANIFEST populated.
- Caller-boundary metadata required at service adapter boundary.
- Governance freeze snapshot and invariant registry present.
- Missing `docs/THREAT_MODEL.md` reference fixed in v0.9.3_STABLE_FIXED.

## Closed / hardened in v0.10.0_CANDIDATE

- Naked `governance.evaluate_task()` invocation fails closed by default unless a trusted entry context is supplied.
- Service adapter supplies the trusted production entry context after caller-boundary validation.
- Runtime boundary hardening evidence verifies direct default denial and adapter-mediated success.

## Closed / hardened in v0.10.1_STABLE

- Direct Governance entry is fail-closed without trusted entry context.
- Public evaluation entry is explicitly classified as `service_adapter`.
- Forbidden caller classes now fail closed in runtime evidence.
- Selected freeze assumptions are covered by executable runtime invariant evidence.

## Closed / hardened in v0.10.2_STABLE / v0.10.3_STABLE

- Runtime chain/order assertions are executable via `src/runtime_chain_assertions.py`.
- Skipped-stage detection is covered by evidence.
- Invalid downstream execution after Enforcement denial fails closed.
- Freeze-aware runtime invariant evidence covers chain/order behavior.

## Closed / hardened in v0.11.0_STABLE / v0.11.3_STABLE

- `pyproject.toml` packaging baseline is present.
- Editable install via `python -m pip install -e .` is supported.
- Console entry points are declared: `gategraph` and `gategraph-server`.
- Packaging, install surface, startup surface and config consistency evidence are present.

## Closed / hardened in v0.12.0_STABLE

- Context is explicitly classified as a governance boundary.
- Context provenance is required and inconsistent provenance fails closed.
- Instruction-like text in untrusted/replay/proposal context remains data.
- Replay/explain context is descriptive-only, non-executable reference context.
- Suspicious context patterns are visibility-only markers, not autonomous filtering.

## Closed / hardened in v0.11.4_STABLE

- Startup/shutdown semantics are explicitly covered by evidence.
- Config/runtime mismatch detection is explicitly covered by evidence.
- Runtime surface freeze coupling is explicitly covered by evidence.
- Unsupported runtime mutations, startup overrides, operational shortcuts and config bypasses are documented.
- Release-process guard now checks CHANGELOG duplicate current headers, known-gaps roadmap release claims and HTTP server version string consistency.

## Still open – product/deployment

- HTTP adapter has no built-in Auth/TLS; reverse-proxy/auth reference architecture remains future work.
- No KMS-backed secret management.
- Capability-token signing remains symmetric HMAC.
- SQLite remains single-node storage.
- No Docker/Systemd deployment baseline.
- No external framework integration examples.
- No UI/dashboard.
- No operator alert routing integration.
- No audit-log retention management.
- No security-disclosure process.

## Non-scope for v0.12.0_STABLE

- no new agents
- no new adapters
- no distributed governance
- no new runtime execution model
- no new governance decision path
- no product UI
- no Docker/Kubernetes/Helm/service mesh
- no memory system
- no vector database
- no embeddings
- no semantic scoring
- no autonomous context filtering
- no AI content moderation

Current release surface: v0.12.7_STABLE


Release surface: v0.12.8_STABLE.

Release surface: v0.12.9_STABLE.
