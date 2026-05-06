# Scale Safety (v0.8.3)

## Purpose

v0.8.3 fixes scale-relevant findings from review:

1. Session-budget TOCTOU risk
2. Projected-vs-actual cost divergence
3. Fragile reason substring matching
4. Stale event schema version
5. Outdated README status

## Fixes

### Session-budget TOCTOU

`session_budget_guard.evaluate_before_task()` now starts budget evaluation with `BEGIN IMMEDIATE` when no caller transaction is active.

This serializes the read-budget/write-link sequence for SQLite-based PoC deployments.

### Cost reservation

Allowed session tasks now reserve `projected_cost_units` in `session_task_links.reserved_cost_units`.

Session aggregation uses:

```text
max(reserved_cost_units, actual_runtime_cost)
```

This means:

- future tasks see projected cost immediately
- actual runtime overrun is reflected on later checks
- underestimation cannot hide from the next session-budget check

### Reason normalization

Reason normalization now uses explicit `(stage, canonical_reason_key)` mapping instead of broad substring matching.

### Schema version

New audit events use `schema_version = 0.8.3`.

## Remaining boundary

This is still a SQLite PoC, not a distributed budget ledger. Scaling across services would require an external transactional store or ledger-backed reservation model.
