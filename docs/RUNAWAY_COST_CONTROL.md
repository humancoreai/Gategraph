# Runaway / Cost Control — Runtime Governance v1

Status: v0.8.25.1 stable  
Scope: deterministic runtime hardening for cost, loop and step escalation.

## Purpose

Runtime Governance closes the gap between valid actions and too many valid actions.

It does not replace Enforcement, Session Budget Guard or Runtime Guard. It computes a stricter runtime state from already-known budget facts and returns constraints that the Runtime Guard can enforce before a step is recorded.

## Invariants

- Enforcement remains the only Gatekeeper for capabilities.
- Guards never grant permission; they can only preserve an already allowed path or stop it.
- Runtime Governance never mutates rules, budgets, tokens, secrets or policies.
- Pattern/loop signals may only tighten constraints.
- Missing or invalid budget facts fail closed.

## Escalation states

Runtime Governance uses a deterministic state machine:

```text
normal -> degraded -> throttled -> blocked
```

State inputs:

- used cost / max cost
- used steps / max steps
- repeated action count / repeated action limit
- optional loop signal

Thresholds:

- below 70%: `normal`
- 70% or more: `degraded`
- 90% or more: `throttled`
- exhausted or invalid budget: `blocked`

A loop signal escalates by exactly one state. It cannot de-escalate.

## Constraint output

The computed state returns:

- `state`
- `reason`
- `max_cost_for_action`
- `remaining_steps`
- `remaining_cost_units`

The Runtime Guard blocks when the requested action cost exceeds `max_cost_for_action`.

## Behavior

- `normal`: action may use remaining budget.
- `degraded`: action size is reduced to at most half of remaining cost.
- `throttled`: only minimal cost action (`1`) may pass.
- `blocked`: no action may pass.

## Evidence

`tests/runaway_cost_evidence.py` now covers:

- negative session projected cost fails closed
- zero runtime cost fails closed without step creation
- negative external API projected cost stops before runtime/action path
- near-budget high-cost follow-up is blocked before step creation
- loop signal tightens constraints and cannot grant continuation

## Non-goals

- No distributed budget.
- No real provider billing integration.
- No monitoring/alerting.
- No adaptive model-based optimization.
- No automatic proposal/application path.
