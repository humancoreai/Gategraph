# GateGraph v0.8.26_STABLE

Focus: Cross-Session Budget Control.

## Summary

This stable release extends `v0.8.25.1_STABLE` with a Governance-owned budget ledger to prevent budget bypass by splitting work across multiple tasks/sessions.

## Added

- Budget ledger component
- Hierarchical budget scope model
- Idempotent budget reservations
- Reservation consume/release/expiry lifecycle
- Budget claims inside signed capability tokens
- Enforcement validation of token budget claims
- Cross-session budget evidence tests

## Not included

- real distributed budget coordination
- external provider billing integration
- monitoring/alerting UI
- real KMS

## Validation performed here

- `python -S -m py_compile src/*.py tests/cross_session_budget_evidence.py tests/evidence_ci.py`
- `python -S tests/cross_session_budget_evidence.py`

Result: cross-session budget evidence passed.

## Validation still required before declaring stable

Run full evidence suite on the target Windows environment:

```powershell
python tests\evidence_ci.py
```

Only promote to stable if the full evidence runner reports all checks passed.
