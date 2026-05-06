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
