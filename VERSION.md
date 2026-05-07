# GateGraph Version

Current stable release: v0.8.29_STABLE

Base: v0.8.28_STABLE

Stable scope:

- Read-only Operational Alert evaluation on top of append-only incidents.
- `OperationalAlert` model and deterministic alert sorting by severity.
- `evaluate_operational_alerts(...)` and `evaluate_open_operational_alerts(...)`.
- Evidence proving alerts do not repair, unblock, acknowledge, resolve, or mutate budget scopes.

Validation:

- Full Windows Evidence CI passed: True.
- Operational alerting evidence passed: 4/4.
- Unexpected allows: 0.
- Invariant violations: 0.

### Boundary

This stable release adds operational visibility only. It does not add automated incident recovery, monitoring transport, notification delivery, or new enforcement behavior.
