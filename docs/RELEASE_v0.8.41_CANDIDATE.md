# GateGraph v0.8.41_CANDIDATE

## Phase 9: Failure Analysis / Postmortem Layer

## Base

Built on:

- `v0.8.40_STABLE`

## Goal

Make recurring failure structures visible across stored decision/audit-like event data without changing system behavior.

## Scope

Implemented read-only descriptive helpers:

- Pattern Detection
  - counts by normalized reason code
  - counts by guard
  - counts by guard + reason
  - time bucket distribution
- Comparative Analysis
  - decision grouping
  - guard grouping
- Lightweight Failure Clustering
  - grouping by reason code + guard + decision
  - no ML
  - no scoring
  - no ranking
- Postmortem View
  - filter by guard / reason / decision
  - case count
  - reason groups
  - decision sequence groups
  - time distribution
- Timeline Correlation View
  - descriptive time buckets
  - optional cost/runtime values displayed as raw values only

## Invariants

The Failure Analysis Layer may:

- group data
- count data
- compare data
- expose descriptive structure

It must not:

- affect Governance logic
- affect Enforcement logic
- mutate Audit/Core data
- rank failures
- recommend actions
- infer root cause
- introduce ML/heuristic scoring

## Evidence

Added:

```powershell
python tests\failure_analysis_evidence.py
```

Expected result:

```text
PASS failure_analysis_evidence
```

Integrated into Evidence CI when the local runner list supports direct insertion.

## Blockers

None known inside the v0.8.41 scope.

## Unverified

- Full Windows Evidence CI must be run by operator.
- Integration with downstream operator UI remains outside this phase.

## Implementation Traps

- Frequency is not importance.
- Cluster is not cause.
- Timeline correlation is not causation.
- Output labels must not imply ranking or recommendations.
