# DEVLOG

## v0.4.2

Fixes after 20-run comparative validation:

- added revoked-token DB check in `enforcement.py`
- fixed critical-risk behavior via `RULE-005`
- fixed `data_sensitivity=secret` priority in `risk_engine.py`
- preserved task-binding enforcement
- extended validation to 20 scenarios in isolated and accumulated modes

Validation result:

```text
Passed: isolated 20/20 | accumulated 20/20
Failed: 0
Unexpected allows: 0
Invariant violations: 0
DB events accumulated: 31
```

## v0.4.1

- added task-binding check in enforcement
- added cross-task token reuse validation

## v0.4.0

- initial PoC implementation based on GateGraph v0.4 spec

## v0.4.3 — Usage simulation semantic fixes

- Risk Engine: `api_call` with `input_source="external"` now classifies as `medium`.
- Risk Engine: `data_sensitivity="secret"` is evaluated before write/delete and always classifies as `critical`.
- Governance: `require_review` now issues an analysis-only token when requested capability is `read_files`.
- `require_review` still denies side-effect capabilities (`write_files`, `delete_files`, `api_call`).
- No architecture changes; only semantic alignment with v0.4 intent.
