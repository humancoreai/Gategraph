# GateGraph v0.8.44_STABLE — Governance Drift Detection

## Scope

Adds descriptive governance drift visibility on top of historical audit/operator data.

## Added

- Governance baseline snapshots for reason, guard, queue and workflow distributions
- Descriptive snapshot comparison engine
- Append-only drift event log
- Queue/reason co-occurrence view
- Workflow distribution snapshot
- `drift_detection_evidence`

## Invariants

- Drift data is descriptive only
- No policy mutation
- No decision influence
- No automatic reaction
- No cause assertion
- No evaluation labels, score fields or recommendation fields

## Evidence

- `tests/drift_detection_evidence.py` passed locally
- Full Windows Evidence CI required before stable promotion
