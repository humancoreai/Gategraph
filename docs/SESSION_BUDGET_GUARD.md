# Session Budget Guard (v0.8)

## Purpose

The Session Budget Guard closes the documented v0.7.3 gap where many individually valid tasks could accumulate cost across task/session/agent boundaries.

## Scope

- Additive runtime guard layer.
- Does not grant capabilities.
- Does not change Governance, Enforcement, Audit, or Pattern Engine semantics.
- Stops fresh task work before per-task runtime budgets can hide cumulative drift.

## Controls

- `max_session_cost_units`
- `max_session_tasks`
- `max_agent_cost_units`

## Tables

- `session_budgets`
- `session_task_links`
- `session_budget_decisions`

## Invariants

- Missing explicit session budget evaluation fails closed.
- Session guard can stop, never allow capabilities.
- Enforcement remains the only action gatekeeper.
- Runtime Guard remains per-task.
- Pattern Engine remains proposal-only.

## Evidence

`tests/session_budget_evidence.py` proves:

- cross-task cascades stop at session budget
- multi-agent aggregate drift stops at session budget
- session reset continuity is blocked
- micro-task floods stop at session budget
- per-agent budget stops one expensive actor
- missing session budget fails closed
