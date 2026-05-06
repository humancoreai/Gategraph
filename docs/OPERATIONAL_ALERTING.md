# Operational Alerting

## Purpose

Operational Alerting makes existing operational incidents visible as prioritized signals.
It does **not** add autonomy, recovery, enforcement, notification transport, or policy mutation.

## Position in the architecture

Operational Alerting sits above `operational_hardening.py` incidents:

```text
Budget Snapshot / Audit Replay
        ↓
Append-only Incident Records
        ↓
Read-only Alert Evaluation
```

## Invariants

- Alerts are read-only signals.
- Alerts never allow, block, repair, acknowledge, or resolve incidents.
- Alerts never mutate Budget Ledger state.
- Alerts never change Governance, Runtime, Enforcement, Pattern Engine, or Review Workflow behavior.

## Alert model

Each alert contains:

- `alert_id`
- `severity`
- `reason_code`
- `trigger_type`
- `trigger_ref`
- `message`
- `created_at`

## Severity ordering

Alerts are sorted by deterministic severity priority:

1. `critical`
2. `high`
3. `medium`
4. `low`

## Scope boundary

This is intentionally not monitoring infrastructure.
No email, webhook, UI, scheduler, daemon, background worker, retry mechanism, or automatic mitigation is included in this gate.
