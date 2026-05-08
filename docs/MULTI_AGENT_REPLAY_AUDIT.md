# Multi-Agent Replay / Audit Model — v0.9.2_STABLE

## Status

This model extends explainability vocabulary only. It does not add distributed execution.

## Trace Model

Required identifiers:

- trace_id: root execution/replay identity
- causal_event_id: append-only audit event
- parent_event_id: optional causal predecessor
- agent_id: runtime identity
- mode_id: applied constraint profile
- task_id: governed task
- delegation_id: optional parent-child link
- decision_id: governance decision
- token_id: enforcement token reference

## Causal Ordering

Audit reconstruction must support deterministic ordering by:

1. trace_id
2. causal parent relation
3. append-only event order
4. deterministic tie-breaker for same-level events

## Explainability Requirements

Multi-agent explanation must answer:

- who acted?
- under which mode?
- who delegated?
- what was the parent authority?
- which budget scope was used?
- which capability was narrowed?
- which guard stopped or allowed execution?
- what human review state applied?

## Replay Invariant

Replay must never infer hidden state. If reconstruction requires unaudited state, replay fails closed as incomplete.
