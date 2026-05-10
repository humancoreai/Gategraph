# Cross-Session Budget Control

Status: implemented as stable extension on top of `v0.8.25.1_STABLE`.

## Purpose

Cross-session budget control prevents agents from bypassing cost/runtime limits by splitting one large job into many small tasks or sessions.

## Architecture

Budget authority remains in the Governance Layer.

Flow:

```text
Governance -> Budget Ledger reservation -> Capability Token -> Enforcement -> Runtime
```

Runtime and Enforcement do not compute or expand budget. They only verify signed token claims and stop/reject invalid execution paths.

## New component

`src/budget_ledger.py`

Responsibilities:

- create and read budget scopes
- reserve budget atomically
- consume or release reservations
- expire stale reservations
- derive deterministic escalation states

## New persistence

Tables:

- `budget_scopes`
- `budget_reservations`

Scope types:

- `system`
- `actor`
- `task`
- `session`

## Token changes

Capability tokens now optionally carry budget claims:

- `budget_scope_id`
- `budget_reservation_id`
- `max_cost_for_action`
- `escalation_state`

These claims are included in the HMAC signature.

## Evidence

New evidence file:

`tests/cross_session_budget_evidence.py`

Covered cases:

- cross-session split attack
- reservation idempotency
- stale reservation expiry/release
- token budget claim enforcement
- fail-closed missing scope

## Limits

This is still single-node local ledger logic. It is not a distributed consensus or multi-node budget system.


## Stable evidence

Promoted in `v0.8.26_STABLE` after full Windows Evidence CI reported `Passed: True` on 2026-04-28.
