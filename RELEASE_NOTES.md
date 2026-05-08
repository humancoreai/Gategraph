# Release Notes – v0.10.2_STABLE

## Summary

v0.10.2_STABLE continues Phase A: Runtime / Boundary Hardening.

It makes the guard-chain order executable and explicitly fails closed for skipped stages, invalid enforcement chains, duplicate stages, unknown stages, and action-ready claims without the complete guard sequence.

## Added

- `src/runtime_chain_assertions.py`
- `tests/runtime_chain_order_evidence.py`
- `docs/RUNTIME_CHAIN_ASSERTIONS.md`

## Updated

- `src/guard_orchestrator.py` records evaluated guard stages and chain assertion evidence.
- `tests/freeze_runtime_invariant_evidence.py` now verifies runtime chain assertions as executable freeze-aware behavior.
- `tests/evidence_ci.py` includes runtime chain/order evidence.
- release metadata and release integrity evidence target v0.10.2_STABLE.

## Unchanged

- no new runtime capability
- no new governance authority
- no new adapter
- no new agentic behavior
- no packaging/deployment layer
- no UI
