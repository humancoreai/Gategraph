# GateGraph Test Report — v0.5 PoC

## 1. Test scope

Three simulation phases were executed:

1. Normal usage simulation
2. Unusual input simulation
3. Agent scenario simulation

The goal was not performance testing. The goal was invariant validation.

---

## 2. Normal usage simulation

Summary:

```text
Runs: 10
Unexpected allows: 0
Invariant violations: 0
```

Covered:

- local file reads
- local source reads
- write attempts
- delete attempts
- untrusted document read
- secret config read
- external API call
- unknown action

Result:

```text
passed
```

---

## 3. Unusual input simulation

Summary:

```text
Runs: 12
Unsafe allows: 0
Invariant violations: 0
```

Covered:

- empty capabilities
- unknown capability
- mixed read/write request
- duplicate capabilities
- case mismatch
- empty input source
- unknown input source
- unknown sensitivity
- secret + untrusted
- secrets + unknown capability
- uppercase external input source
- very long capability name

Result:

```text
passed
```

---

## 4. Agent scenario simulation

Summary:

```text
Runs: 12
Unexpected allows: 0
Invariant violations: 0
```

Covered:

- agent reads repo files
- agent proposes patch
- agent attempts direct write
- agent attempts delete
- agent reads untrusted document
- agent follows untrusted write instruction
- agent handles secret config
- agent external API call
- unknown tool request
- mixed read/write request
- prompt-injection-like untrusted read

Result:

```text
passed
```

---

## 5. Current interpretation

GateGraph v0.5 successfully validates:

```text
- no write without approval
- no delete without approval
- no external API execution
- no unknown tool execution
- no critical-risk execution
- no cross-task token reuse
- no revoked-token execution
- no unsafe allows in tested flows
```

---

## 6. Remaining non-test gaps

The following are not test failures but future work:

- runtime/cost control
- pattern engine
- token signing
- production concurrency
- real approval workflow
- graph query API

## Runtime / Audit Evidence Report – v0.7.1

Added a dedicated evidence runner:

```bash
python tests/runtime_stress_evidence.py
```

Output path:

```text
tests/logs/runtime_evidence_<timestamp>.json
```

### Evidence scenarios

| Scenario | Result | Evidence source |
|---|---:|---|
| agent_pingpong_loop | PASS | runtime_decisions + runtime_steps |
| many_allowed_micro_actions_cost_limit | PASS | runtime_decisions + runtime_steps |
| valid_token_but_runtime_exceeded | PASS | governance event + token + runtime_decision |
| no_action_without_token | PASS | enforcement_rejection event |
| pattern_engine_proposal_only | PASS | proposals table + active rule count |
| repeated_same_decision_evidence | PASS | idempotent governance event evidence |

### Latest local verification

- Core loop tests: 20/20 passed in isolated and accumulated mode.
- Runtime Guard tests: 6/6 passed.
- Pattern Engine tests: 3/3 passed.
- Agent scenario simulation: 12 runs, 0 invariant violations.
- Usage simulation: 10 runs, 0 invariant violations.
- Unusual input simulation: 12 runs, 0 invariant violations.
- Runtime/Audit evidence runner: 6/6 passed.

### Notes

Runtime Guard evidence is stored in runtime-specific tables, not in the normal `events` table. The evidence runner intentionally merges both views into one JSON proof log without changing core behavior.

## v0.7.2 CI Evidence Update

Added CI-ready evidence execution via:

```bash
python tests/evidence_ci.py
```

The runner executes:

- `tests/runtime_stress_evidence.py`
- `tests/test_loop.py`
- `tests/runtime_guard_tests.py`
- `tests/pattern_engine_tests.py`
- `tests/usage_simulation.py`
- `tests/unusual_inputs.py`
- `tests/agent_scenarios.py`

It writes a machine-readable summary to:

```text
tests/logs/ci_evidence_<timestamp>.json
```

Additional runtime evidence scenarios now cover:

- alternating multi-agent delegation stopped by task-level `max_steps`
- fail-closed behavior when no runtime budget exists
- exact cost-boundary behavior
- current limitation: cost budget is per-task, not session-global

The last point is intentionally logged as a medium-severity known gap, not as a failing test, because implementing a session/global budget would change production scope.


## v0.7.3 Phase 3B / Cross-Task Drift Evidence

Added evidence tests for real-world cost/resource drift that can occur even when every individual task remains valid.

Expected result:
- The system should not violate core invariants.
- Evidence should reveal that cumulative costs are not currently blocked across task/session/agent boundaries.

Outcome classification:
- Finding severity: medium/high depending on scenario.
- Type: documented design boundary.
- Not a production core regression.


## v0.8.0 Session Budget Guard Evidence

Added tests:
- cross_task_cascade_stopped_by_session_budget
- parallel_multi_agent_stopped_by_session_budget
- session_reset_continuity_stopped
- micro_task_flood_stopped_by_session_budget
- agent_budget_stops_single_agent_drift
- missing_session_budget_fail_closed

Expected:
- v0.7.3 drift findings now stop at session/global/agent budget boundaries.
- Existing evidence and CI tests remain green.


## v0.8.1 Guard Orchestration Evidence

Added tests:
- enforcement_blocks_before_budget_guards
- session_stops_before_runtime_guard
- runtime_stops_when_session_allows
- both_session_and_runtime_would_stop_session_priority
- all_guards_pass_action_ready

Expected:
- Deterministic stop priority.
- No misleading duplicate stop reasons.
- No runtime work after session/global exhaustion.


## v0.8.2 Reason Normalization Evidence

Added tests:
- normalizes_known_reasons
- unknown_reason_falls_back_safely
- orchestrator_outputs_normalized_enforcement_stop
- orchestrator_outputs_normalized_session_stop
- orchestrator_outputs_normalized_runtime_stop
- orchestrator_outputs_normalized_action_ready

Expected:
- Stable explain codes without changing decisions.
- Raw reasons preserved.
- Unknown reasons safely classified as unclassified.


## v0.8.3 Scale Safety Evidence

Added tests:
- reserved_cost_prevents_two_tasks_oversubscribe
- actual_cost_drift_blocks_next_task
- reason_normalizer_uses_canonical_prefix
- event_schema_version_current

Expected:
- Projected cost is reserved immediately.
- Actual runtime overrun blocks later session work.
- Reason normalization uses stable canonical keys.
- New audit events use schema version 0.8.3.


## v0.8.4 External API Mock Evidence

Added tests:
- allowed_mock_call_completed
- no_token_blocks_before_api
- session_budget_blocks_expensive_api
- runtime_budget_blocks_repeated_api
- api_timeout_audited_as_failure
- api_rate_limit_audited_as_failure
- untrusted_api_response_is_data

Expected:
- External mock calls only execute after guard pipeline action-ready.
- Blocked calls are audited without simulated execution.
- API failures are audited as execution failures.

## v0.8.5 API Enforcement Binding

Updated external API evidence to prove the adapter calls Enforcement internally.

Result:
- External API Evidence: 7/7 passed
- No-token path stops at Enforcement before Session/Runtime guards
- Allowed paths require a real valid API capability token


## v0.8.5 Hygiene Fix

Non-semantic cleanup after external API enforcement binding:

- Updated legacy simulation headers from v0.4.x to v0.8.5.
- Kept audit `schema_version = 0.8.3` intentionally; no audit schema migration occurred in v0.8.4/v0.8.5.
- Updated `actor_version` to 0.8.5 for newly logged events.
- CI/evidence runner uses `python -S -u` for deterministic subprocess execution in local and CI environments.

No governance, enforcement, runtime, session-budget, pattern-engine, or adapter semantics changed.


## v0.8.6 Runaway Cost Evidence

Added `tests/runaway_cost_evidence.py` covering negative projected costs, zero runtime costs, and negative-cost External API requests. Targeted run: 3/3 passed. Individual evidence scripts passed; aggregate runner instability is documented in `RELEASE_STATUS.md`.


## v0.8.9 Key Rotation Evidence

Added tests for active-key issuance, legacy-key verification while trusted, legacy-key retirement fail-closed behavior, and signing-key-ID tamper rejection.

## v0.8.11 Secret/API Integration Evidence

Added `tests/secret_api_integration_evidence.py`.

Coverage:

- scoped env secret reaches transport only after Enforcement + Session Budget + Runtime Guard pass
- raw secret value is not written to audit evidence
- missing secret blocks before transport
- endpoint scope mismatch blocks before transport
- no-token path blocks at Enforcement before secret resolution

Result during local validation: 4/4 passed.
