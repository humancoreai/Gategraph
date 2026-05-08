# GateGraph v0.8.41_STABLE

## Phase 9: Failure Analysis / Postmortem Layer

## Base

- `v0.8.40_STABLE`

## Windows Evidence CI

Operator-reported full Evidence CI:

```text
Passed: True
```

## Stable Scope

Implemented a read-only Failure Analysis / Postmortem Layer:

- Pattern Detection
  - reason-code counts
  - guard counts
  - guard + reason counts
  - time bucket distribution
- Comparative Analysis
  - decision grouping
  - guard grouping
- Lightweight Failure Clustering
  - grouping by `normalized_reason.code`, `guard`, `decision`
  - no ranking
  - no scoring
  - no ML
- Postmortem View
  - filtered descriptive summary by guard / reason / decision
  - case count
  - reason groups
  - decision-sequence groups
  - time distribution
- Timeline Correlation View
  - descriptive time buckets
  - raw cost/runtime values only

## Stable Fixes

- Fixed Evidence CI manifest integration for `failure_analysis_evidence`.
- Preserved Windows-safe test behavior from v0.8.40.

## Invariants

- No Governance Core change.
- No Enforcement logic change.
- No Runtime Guard behavior change.
- No Audit/Core mutation.
- No automatic root-cause analysis.
- No recommendation output.
- No hidden prioritization.
- No policy tuning.

## Known Implementation Guardrails

- Frequency is not importance.
- Cluster is not cause.
- Timeline correlation is not causation.
- Descriptive grouping must remain separate from operator interpretation.

## Repo Hygiene

Generated artifacts excluded from this stable archive:

- `tests/logs/`
- `*.db`
- SQLite runtime files
- `__pycache__/`
- `*.pyc`
- `.pytest_cache/`
