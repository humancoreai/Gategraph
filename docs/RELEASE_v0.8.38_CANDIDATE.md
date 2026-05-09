# GateGraph v0.8.38_CANDIDATE

## Phase
Runtime Cost Governance / Kill Conditions

## Base
v0.8.36_STABLE

## Scope
This candidate adds deterministic pre-flight runtime cost governance without changing the API contract or Governance Core.

## Added
- `src/runtime_cost_guard.py`
- `tests/runtime_cost_governance_evidence.py`

## Changed
- `src/runtime_guard.py`
  - delegates projected runtime cost / loop kill checks to Runtime Cost Guard before recording a step
- `src/reason_normalizer.py`
  - adds stable reason codes for projected runtime cost, projected step, throttling, loop detection, and escalation limit stops
- `tests/evidence_ci.py`
  - includes Runtime Cost Governance evidence in the manifest

## Invariants
- No API schema change
- No new API fields
- No Core Governance reinterpretation
- Runtime Cost Guard can only stop; it cannot grant capability
- Invalid projected cost fails closed

## Evidence
Local targeted evidence passed:
- `tests/runtime_cost_governance_evidence.py`
- `tests/runaway_cost_evidence.py`
- `tests/runtime_guard_tests.py`

Full Windows Evidence CI is still required before STABLE promotion.
