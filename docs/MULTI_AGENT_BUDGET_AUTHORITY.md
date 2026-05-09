# Multi-Agent Budget Authority — v0.9.2_STABLE

## Status

Budget authority remains central and non-delegable.

## Budget Ownership

Only the central governance/budget ledger may authorize budget scopes.

Agents may:

- consume budget after approval
- request reservation against an existing scope
- operate under narrowed delegated limits

Agents may not:

- mint budget
- merge budgets
- split budgets without central reservation
- borrow from siblings
- extend limits after degradation
- create implicit pooled budgets

## Anti Budget-Emergence Rules

1. Every child budget must reference a parent authorized scope.
2. Sum of child reservations must never exceed parent available budget.
3. Released budget returns only to the parent scope, never to an agent wallet.
4. Budget reservations are idempotent by reservation_id.
5. Cross-agent budget transfer without central ledger event is forbidden.
6. Budget exhaustion is terminal until a human or central policy grants a new scope.

## Audit Requirements

Every reservation, consume, release, throttle, degradation, and block state must be audit-visible and trace-linked.
