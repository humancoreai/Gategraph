# Reason Normalization (v0.8.2)

## Purpose

Raw stop reasons are useful for debugging, but brittle for automation, UI, reports, and CI evidence.

Reason normalization adds stable explain metadata:

- `code`
- `category`
- `severity`
- `stage`
- `message`
- `raw_reason`
- `priority`

## Invariants

- Normalization never changes decisions.
- Raw reasons are preserved.
- Unknown reasons fail into an `*_UNCLASSIFIED` code, not into an exception.
- Normalization is additive explain metadata only.

## Examples

| Stage | Raw fragment | Code |
|---|---|---|
| enforcement | no capability token | ENF_NO_TOKEN |
| session_budget | max_session_cost_units | SES_COST_LIMIT |
| session_budget | max_agent_cost_units | SES_AGENT_COST_LIMIT |
| runtime_guard | max_steps | RT_STEP_LIMIT |
| runtime_guard | max_cost_units | RT_COST_LIMIT |
| runtime_guard | repeated_action_limit | RT_REPEATED_ACTION |
| action_ready | all guards passed | OK_ACTION_READY |

## Evidence

`tests/reason_normalization_evidence.py` proves:

- known reasons map deterministically
- raw reasons remain preserved
- unknown reasons use safe fallback
- Guard Orchestrator emits normalized reasons for enforcement/session/runtime/action-ready outcomes
