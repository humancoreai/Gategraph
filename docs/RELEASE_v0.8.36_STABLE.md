# GateGraph v0.8.36_STABLE

## Phase
API Robustness / Real-World Stability.

## Base
GateGraph v0.8.35_STABLE.

## Stable Promotion
Promoted from v0.8.36_CANDIDATE after Full Windows Evidence CI passed on 2026-04-29.

## Confirmed Evidence
- evidence_runner_selftest: PASS
- api_contract_evidence: PASS
- api_robustness_evidence: PASS
- server_mode_evidence: PASS
- server_hardening_evidence: PASS
- repo_push_hygiene_evidence: PASS
- full aggregate evidence_ci: PASS

## Stability Scope
- Parallel request stability.
- Large and invalid payload handling.
- Invalid JSON and wrong content type handling.
- Aborted connection handling without server crash.
- Deterministic response structure under stress.
- Light connection hardening.

## Invariants Preserved
- API response contract unchanged.
- No new response fields introduced.
- Core governance logic unchanged.
- Server remains an adapter.
- Fail-closed behavior preserved.

## Known Non-Scope
- Authentication / API keys.
- Rate limiting.
- Multi-node operation.
- Load balancer behavior.
- Streaming.
- Production-scale performance optimization.
