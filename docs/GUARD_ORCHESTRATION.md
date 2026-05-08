# Guard Orchestration (v0.8.1)

## Purpose

GateGraph now has multiple stop-capable protection layers. This document fixes the deterministic order.

## Pipeline

1. Enforcement result must already allow the action.
2. Session Budget Guard checks aggregate session/agent/task budget.
3. Runtime Guard checks per-task step/runtime/cost budget.
4. Action may proceed only if all prior gates pass.

## Invariants

- Enforcement remains the only action gatekeeper.
- Session Budget Guard never grants capabilities.
- Runtime Guard never grants capabilities.
- Pattern Engine remains proposal-only.
- Earliest stop wins.
- Exactly one authoritative stop stage is reported.

## Stop priority

1. `enforcement`
2. `session_budget`
3. `runtime_guard`
4. `action_ready`

## Evidence

`tests/guard_orchestration_evidence.py` proves:

- Enforcement block prevents Session/Runtime checks.
- Session Budget stop prevents Runtime Guard evaluation.
- Runtime Guard can stop after Session Budget allows.
- If both Session and Runtime would stop, Session Budget has priority.
- All guards passing reaches `action_ready`.
