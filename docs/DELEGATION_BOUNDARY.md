# Delegation Boundary — v0.9.2_CANDIDATE

## Status

Delegation is modelled as governed lineage, not as autonomous orchestration.

## Delegation Definition

Delegation is a parent task requesting a child task under stricter or equal constraints.

Required fields:

- delegation_id
- parent_trace_id
- parent_agent_id
- child_agent_id
- parent_task_id
- child_task_id
- delegation_depth
- delegated_budget_scope_id
- capability_narrowing_hash
- governance_decision_id
- capability_token_id

## Delegation Rules

1. Delegation requires a fresh governance decision.
2. Child capability must be equal or narrower than parent capability.
3. Child budget must be reserved from an existing centrally authorized budget scope.
4. Delegation depth must be bounded.
5. Delegation lineage must be replayable from audit events alone.
6. Delegation loops must fail closed.
7. Delegation cannot create new policy or budget authority.

## Deterministic Replay Requirements

Replay must reconstruct:

- parent-child lineage
- causal order
- budget reservation and consumption
- capability narrowing
- human review gates
- terminal decision state

## Fail-Closed Conditions

Delegation fails closed on:

- missing parent trace
- missing governance decision
- missing or broadened capability narrowing
- invalid budget scope
- depth overflow
- lineage cycle
- unaudited communication state
