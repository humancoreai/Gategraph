# Block D — Audit & Explain Evidence

Status: v0.8.16 audit/explain reconstruction evidence.

## Purpose

Block D verifies that GateGraph decisions are not only logged, but reconstructable by a reviewer from persisted evidence.

## Added

- `src/explain_trace.py`: read-only trace builder derived from persisted events/decisions only.
- `tests/block_d_audit_explain_evidence.py`: completed, Enforcement-blocked, HTTP Policy-blocked, and secret-backed reconstruction checks.

## Evidence Scenarios

| Scenario | Expected proof |
|---|---|
| completed flow | action completed after `action_ready` with `OK_ACTION_READY` |
| no-token flow | blocked at Enforcement with `ENF_NO_TOKEN` and no downstream budget/runtime work |
| HTTP policy flow | core guards passed, then HTTP Policy blocked before secret/transport |
| secret-backed flow | action completed, secret ref metadata present, raw secret absent |

## Invariants

- Trace building is read-only.
- Explain output never changes decisions.
- Secret values are not stored or emitted by trace output.
- Audit reconstruction uses persisted evidence, not fresh policy evaluation.

## Known Limits

- Trace format is reviewer-facing PoC output, not a final UI/API contract.
- It reconstructs local SQLite evidence only.
- Distributed causal traces are not supported yet.
