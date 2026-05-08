# GateGraph v0.8.40_STABLE

## Status

Stable release based on v0.8.40_CANDIDATE_WIN_FIX.

## Evidence

Windows Evidence CI reported:

```text
Passed: True
```

## Stable Fix

- Fixed Windows file-lock issue in `operator_evidence`.
- Root cause: temporary SQLite fixture database remained locked on Windows during cleanup.
- Resolution: explicit SQLite connection close in the operator evidence test harness.

## Scope

Operator / Debug Interface remains read-only:

- decision inspection
- trace query
- aggregation drilldown
- explain/operator navigation support

## Invariants

- No change to Governance Core.
- No change to Enforcement logic.
- No behavioral influence from Operator Layer.
- Operator functions remain read-only.
- Existing Evidence CI green on Windows after fix.

## Repo Hygiene

Generated runtime artifacts are excluded from this stable ZIP:

- `tests/logs/`
- `*.db`
- `__pycache__/`
- `*.pyc`
- `.pytest_cache/`
