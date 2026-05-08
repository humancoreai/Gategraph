# Pattern Engine Priority Scoring (v0.8.19)

## Purpose

The Pattern Engine now adds advisory triage metadata to proposals:

- `priority`: P0, P1, P2, or P3
- `score`: bounded numeric review score
- `score_basis`: human-readable scoring inputs

## Non-negotiable invariant

Priority and scoring never change runtime behavior.

The Pattern Engine still must not:

- activate or change rules
- widen HTTP allowlists
- raise budgets
- issue, revoke, or extend tokens
- change secret refs
- execute actions

All proposals remain `pending_review`.

## Scoring model

The score combines three bounded factors:

1. severity of the observed pattern
2. confidence / concentration of matching observations
3. support count

Priority bands:

- P0: score >= 85
- P1: score >= 70
- P2: score >= 50
- P3: lower-priority review item

## Why this exists

The previous Pattern Engine could create proposals, but all proposals had roughly equal review weight.
This version helps a human reviewer decide what to inspect first without giving the Pattern Engine decision authority.

## Evidence

`tests/pattern_priority_scoring_evidence.py` verifies:

1. repeated critical signature tampering becomes P0
2. repeated HTTP policy blocks get review priority but do not widen allowlists
3. stronger support increases score for the same pattern class
4. priority/score metadata is persisted while status remains `pending_review`

## Boundary

This is triage intelligence, not adaptive governance.
