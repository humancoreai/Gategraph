# GateGraph v0.8.30_STABLE

## Status

Stable.

## Scope

Operational Stability Gate A-D.

### A — Alert Aggregator

Groups alerts by exact cause and preserves highest severity.

### B — Incident State Manager

Adds manual forward-only lifecycle:

`open → acknowledged → resolved`

### C — Monitoring Export

Builds a read-only operational report from budget snapshot, incidents, alerts and aggregated alerts.

### D — Flood Guard

Adds deterministic actor-scoped window limits for task count and cost.

Flood Guard runs before session reservation to prevent blocked flood attempts from creating budget side effects.

## Validation

- `operational_stability_evidence`: 5/5 passed.
- `runaway_cost_evidence`: passed after updating expected guard order for v0.8.30.

## Non-goals

- No UI.
- No autonomous recovery.
- No external monitoring integration.
- No self-healing.
