# Runaway / Cost Control Evidence (v0.8.6)

## Scope

This note covers the v0.8.6 hardening pass for runaway-agent and cost-control edge cases.

## Core invariant

No task may create work with zero or negative cost accounting.

## Implemented hardening

- `session_budget_guard.evaluate_before_task(...)` now fails closed when `projected_cost_units <= 0`.
- `runtime_guard.evaluate_before_step(...)` now fails closed when `cost_units <= 0`.
- Invalid cost reasons are normalized into stable explain codes:
  - `SES_INVALID_COST`
  - `RT_INVALID_COST`
- External API calls inherit the same guard behavior because projected API cost is evaluated by the Guard Orchestrator before runtime/action execution.

## Why this matters

Zero or negative costs are not normal user input. They are control-plane edge cases. If accepted, they can create invisible work, fake remaining budget, or turn repeated calls into under-accounted runaway behavior.

## Non-goals

- No adaptive pricing.
- No real billing integration.
- No distributed quota system.
- No token signing.

These remain future gates.
