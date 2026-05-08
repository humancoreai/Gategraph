# Release Status - GateGraph v0.8.19-pattern-priority-scoring

Status: Single-node PoC / advisory Pattern Engine triage intelligence.

## Added
- Advisory proposal triage metadata:
  - `priority` (`P0`, `P1`, `P2`, `P3`)
  - `score`
  - `score_basis`
- Proposal schema columns for priority/score metadata.
- `tests/pattern_priority_scoring_evidence.py`.
- `docs/PATTERN_ENGINE_PRIORITY_SCORING.md`.

## Changed
- Pattern proposals are now easier to review in risk order.
- Repeated critical token/signature abuse can surface as P0 advisory proposal.
- Repeated high-severity HTTP/secret problems surface as review-priority proposals.
- Support count can raise score within the same pattern class.

## Unchanged
- Pattern Engine remains proposal-only.
- Enforcement remains the only authorization gatekeeper.
- Guards still only stop, never allow.
- No rules, HTTP policies, budgets, tokens, secrets, or actions are mutated by Pattern Engine scoring.
- Production governance/enforcement/runtime semantics unchanged.

## Evidence
- Pattern Priority Scoring Evidence: 4/4 passed.
- Pattern Intelligence Evidence: 4/4 passed.
- Pattern Engine regression tests: 3/3 passed.
- Block D Audit/Explain regression: 4/4 passed.

## Known Limits
- Score is reviewer triage metadata, not causal proof.
- No automatic rule updates or adaptive policy changes.
- No distributed pattern correlation.
- Aggregate runner remains environment-sensitive in local runs.
