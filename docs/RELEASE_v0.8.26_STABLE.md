# GateGraph v0.8.26_STABLE

## Status

`v0.8.26_CROSS_SESSION_BUDGET_CANDIDATE` was promoted to `v0.8.26_STABLE` after a full Windows Evidence CI run reported `Passed: True` on 2026-04-28.

## Release focus

Cross-Session Budget Control closes the budget-bypass gap where an agent could split work across multiple tasks or sessions to avoid per-task limits.

## Added / stabilized

- `src/budget_ledger.py` as single-node Budget Ledger.
- `budget_scopes` and `budget_reservations` schema tables.
- Governance-side budget reservation before token issuance.
- Capability Token budget claims.
- Enforcement-side verification of persisted budget token claims.
- Cross-session evidence coverage for split attacks, reservation idempotency, reservation expiry, token budget-claim enforcement, and missing-scope fail-closed behavior.

## Preserved invariants

- No action without a valid Capability Token.
- Enforcement remains the only action gatekeeper.
- Runtime reads signed constraints and may stop, but does not decide or expand budget.
- Pattern Engine remains advisory and cannot modify budgets, tokens, rules, secrets, or actions.
- Missing or invalid budget scope fails closed.
- Audit/Explain remains reconstructable through stable reason codes and raw reason preservation.

## Evidence summary

Full Windows Evidence CI result: `Passed: True`.

Covered evidence groups include:

- evidence runner selftest
- runtime stress
- session budget
- guard orchestration
- reason normalization
- scale safety
- external API
- runaway cost
- cross-session budget
- capability token hardening
- key rotation
- secret/API integration
- HTTP policy
- security finesse
- block C stress
- block D audit/explain
- core loop
- runtime guard
- pattern engine
- pattern intelligence
- usage simulation
- unusual inputs
- agent scenarios
- controlled apply

Reported critical counters:

```text
CI Evidence: Passed: True
Unexpected allows: 0
Invariant violations: 0
```

## Known limits

- Single-node Budget Ledger only.
- No distributed budget consensus or lock manager.
- No production KMS or OS-keychain lifecycle.
- No real provider billing integration.
- No monitoring/alerting/incident workflow.
- External API execution remains controlled mock/evidence seam.

## Release judgment

Stable for the current local/Windows evidence scope as a deterministic Governance-Core proof of concept. Not production-ready for distributed or operational deployment.
