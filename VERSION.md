# GateGraph Version

Current candidate release: v0.8.29_CANDIDATE

Base: v0.8.28_STABLE

Candidate scope:

- Add read-only Operational Alert evaluation on top of append-only incidents.
- Add `OperationalAlert` model and alert sorting by severity.
- Add `evaluate_operational_alerts(...)` and `evaluate_open_operational_alerts(...)`.
- Add evidence proving alerts do not repair, unblock, acknowledge, resolve, or mutate budget scopes.

Validation:

- Targeted `operational_alerting_evidence` passed: 4/4.
- Full Evidence CI was not completed in this Linux container because the existing runner selftest hangs here; Windows remains the release gate.

### Boundary

This candidate adds operational visibility only. It does not add automated incident recovery, monitoring transport, notification delivery, or new enforcement behavior.
