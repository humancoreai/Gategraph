# GateGraph Runtime Guard — Spec v0.6

**Status:** Draft / design-only  
**Scope:** runtime and cost-control layer for agent-like executions  
**Relationship to GateGraph Core:** separate layer; does not replace Governance, Enforcement, or Audit Graph.

---

## 0. Purpose

GateGraph Core answers:

```text
Is this action allowed?
```

Runtime Guard answers:

```text
May this task continue running?
```

This distinction is important.

GateGraph Core controls permission and capability.  
Runtime Guard controls execution budget, loop behavior, and cost exposure.

---

## 1. Motivation

Agent systems can fail even when every individual action is technically allowed.

Typical failure pattern:

```text
Agent A calls Agent B
Agent B calls Agent A
Both continue exchanging messages
No dangerous tool action occurs
But runtime/cost explodes
```

This is not primarily a permission problem. It is a runtime-control problem.

Runtime Guard exists to prevent:

- runaway agent loops
- unbounded iterations
- excessive runtime
- silent cost growth
- repeated low-value action cycles

---

## 2. Non-goals

Runtime Guard does **not**:

- decide whether a capability is allowed
- change governance rules
- approve write/delete/API actions
- replace enforcement
- analyze semantic truth
- implement billing integration in v0.6
- optimize model quality

---

## 3. Layer model

```text
Task / Agent Step
        ↓
Runtime Guard
        ↓ if budget permits
GateGraph Governance
        ↓ if capability permits
Enforcement
        ↓
Tool / Runtime
        ↓
Audit Event
```

Order matters:

1. Runtime Guard checks whether the task may continue.
2. Governance checks whether the requested action is allowed.
3. Enforcement checks whether the action has a valid capability token.
4. Audit Graph stores what happened.

---

## 4. Core objects

### 4.1 RuntimeBudget

Defines limits for a task.

```json
{
  "budget_id": "BUD-001",
  "task_id": "TASK-001",
  "max_steps": 20,
  "max_runtime_seconds": 300,
  "max_cost_units": 100,
  "repeated_action_limit": 3,
  "created_at": "2026-04-27T12:00:00Z"
}
```

---

### 4.2 RuntimeStep

Represents one controlled execution step.

```json
{
  "step_id": "STEP-001",
  "task_id": "TASK-001",
  "step_index": 4,
  "actor_id": "agent-architect",
  "action_type": "read_files",
  "cost_units": 2,
  "timestamp": "2026-04-27T12:01:00Z"
}
```

---

### 4.3 RuntimeDecision

Result of Runtime Guard evaluation.

```json
{
  "decision": "continue",
  "reason": "within budget",
  "remaining_steps": 16,
  "remaining_cost_units": 92
}
```

Allowed decisions:

```text
continue
warn
stop
escalate
```

---

### 4.4 RuntimeEvent

Append-only audit event for runtime decisions.

```json
{
  "event_id": "RTE-001",
  "schema_version": "0.6",
  "type": "runtime_decision",
  "task_id": "TASK-001",
  "runtime_decision": "stop",
  "reason": "max_steps exceeded",
  "timestamp": "2026-04-27T12:05:00Z"
}
```

Runtime events are stored in the Audit Graph as events, but do not change governance rules.

---

## 5. Runtime limits

### 5.1 max_steps_per_task

Stops tasks after too many steps.

Default for PoC:

```text
max_steps = 20
```

Behavior:

```text
step_count < max_steps  → continue
step_count == max_steps → warn
step_count > max_steps  → stop
```

---

### 5.2 max_runtime_seconds

Stops tasks after too much wall-clock time.

Default for PoC:

```text
max_runtime_seconds = 300
```

Behavior:

```text
elapsed <= max_runtime_seconds → continue
elapsed > max_runtime_seconds  → stop
```

---

### 5.3 max_cost_units

Abstract cost budget.

This is intentionally provider-neutral.

Examples:

```text
1 model call = 1 cost unit
1 file read = 1 cost unit
1 tool call = 2 cost units
1 expensive model call = 10 cost units
```

Default for PoC:

```text
max_cost_units = 100
```

---

### 5.4 repeated_action_limit

Detects repeated identical actions within the same task.

Example loop:

```text
read_file A
read_file A
read_file A
read_file A
```

Default for PoC:

```text
repeated_action_limit = 3
```

Behavior:

```text
same action repeated > limit → stop or escalate
```

---

## 6. Loop detection

v0.6 uses simple structural loop detection only.

It does **not** attempt semantic loop detection.

### 6.1 Action signature

Each step gets a signature:

```text
actor_id + action_type + normalized_target
```

Example:

```text
agent-a:message:agent-b
agent-b:message:agent-a
read_files:README.md
```

### 6.2 Detection rule

If the same signature appears more than `repeated_action_limit` times in a task:

```text
RuntimeDecision = stop
```

If two or more actors alternate repeatedly:

```text
agent-a → agent-b
agent-b → agent-a
agent-a → agent-b
agent-b → agent-a
```

Runtime Guard should classify this as:

```text
escalate
```

This remains optional in v0.6 MVP.

---

## 7. Runtime Guard invariants

```text
RT-INV-001: No controlled task runs without a RuntimeBudget.
RT-INV-002: Every controlled step increments step_count.
RT-INV-003: Every controlled step records cost_units.
RT-INV-004: Exceeding max_steps stops the task.
RT-INV-005: Exceeding max_runtime_seconds stops the task.
RT-INV-006: Exceeding max_cost_units stops the task.
RT-INV-007: Repeated identical action beyond limit stops or escalates.
RT-INV-008: Runtime Guard never changes Governance rules.
RT-INV-009: Runtime Guard decisions are logged as append-only events.
RT-INV-010: Runtime stop decisions fail closed.
```

---

## 8. Integration with GateGraph Core

Runtime Guard should run before Governance evaluation for each step.

```text
step request
→ Runtime Guard
→ if continue: Governance
→ if stop/escalate: no Governance call
```

This avoids spending additional model/tool work after a task is already over budget.

---

## 9. Example flow

```text
Task starts
→ RuntimeBudget created
→ Step 1: read README
→ Runtime Guard: continue
→ Governance: allow
→ Enforcement: allow
→ Event logged

...

Step 21:
→ Runtime Guard: stop
→ Governance not called
→ Runtime stop event logged
```

---

## 10. MVP schema additions

Suggested SQLite tables for a later implementation:

```sql
CREATE TABLE runtime_budgets (
  budget_id TEXT PRIMARY KEY,
  task_id TEXT NOT NULL,
  max_steps INTEGER NOT NULL,
  max_runtime_seconds INTEGER NOT NULL,
  max_cost_units INTEGER NOT NULL,
  repeated_action_limit INTEGER NOT NULL,
  created_at TEXT NOT NULL
);
```

```sql
CREATE TABLE runtime_steps (
  step_id TEXT PRIMARY KEY,
  task_id TEXT NOT NULL,
  step_index INTEGER NOT NULL,
  actor_id TEXT NOT NULL,
  action_type TEXT NOT NULL,
  action_signature TEXT NOT NULL,
  cost_units INTEGER NOT NULL,
  timestamp TEXT NOT NULL
);
```

```sql
CREATE TABLE runtime_decisions (
  decision_id TEXT PRIMARY KEY,
  task_id TEXT NOT NULL,
  step_id TEXT,
  decision TEXT NOT NULL,
  reason TEXT NOT NULL,
  created_at TEXT NOT NULL
);
```

---

## 11. Test scenarios for v0.6 implementation

### A — within budget

Expected:

```text
continue
```

### B — max_steps exceeded

Expected:

```text
stop
```

### C — max_runtime exceeded

Expected:

```text
stop
```

### D — max_cost exceeded

Expected:

```text
stop
```

### E — repeated identical action

Expected:

```text
stop or escalate
```

### F — Runtime stop prevents Governance call

Expected:

```text
runtime_event logged
no governance_decision event for blocked step
```

---

## 12. Open decisions

These are intentionally not resolved in the spec-only step:

1. Should warning at `step_count == max_steps` happen, or should stop occur immediately?
2. Should repeated actor ping-pong escalate instead of stop?
3. Should cost units be configured per action type or per caller?
4. Should budgets be global, per task, per actor, or per project?

---

## 13. Recommended v0.6 implementation order

1. Add runtime schema tables.
2. Add `runtime_guard.py`.
3. Add RuntimeBudget creation.
4. Add `record_step()`.
5. Add `evaluate_runtime()`.
6. Add runtime events.
7. Add test loop for budget and loop scenarios.
8. Keep Pattern Engine postponed until Runtime Guard passes tests.

---

## 14. Summary

Runtime Guard is a separate control layer that prevents allowed actions from becoming unbounded executions.

It complements GateGraph Core:

```text
Governance protects permissions.
Enforcement protects actions.
Runtime Guard protects time, cost, and loop behavior.
```
