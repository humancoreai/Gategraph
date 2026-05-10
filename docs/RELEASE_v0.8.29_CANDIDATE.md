# Release v0.8.29_CANDIDATE

## Scope

Operational visibility extension after `v0.8.28_STABLE`.

## Added

- `OperationalAlert` dataclass.
- `evaluate_operational_alerts(incidents)` pure read-only alert evaluation.
- `evaluate_open_operational_alerts(conn)` for open incident inspection.
- Deterministic severity ordering.
- `tests/operational_alerting_evidence.py`.
- `docs/OPERATIONAL_ALERTING.md`.

## Unchanged

- Enforcement remains the only gatekeeper.
- Governance remains the only decision authority.
- Runtime remains non-decisional.
- Pattern Engine remains proposal-only.
- Review Workflow still applies nothing automatically.
- Budget Ledger authority is unchanged.

## Validation

Targeted evidence:

```text
OPERATIONAL ALERTING EVIDENCE REPORT
Summary: {'total': 4, 'passed': 4, 'failed': 0, 'findings': 0}
```

Full Evidence CI was attempted in this Linux container but did not complete because the existing runner selftest hangs here. Promotion to stable requires the normal Windows full Evidence CI run.

## Boundary

This candidate does not implement:

- automated recovery
- external monitoring transport
- alert delivery
- UI
- new agent logic
- new external API integration
