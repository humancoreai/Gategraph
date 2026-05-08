# GateGraph

**GateGraph** is a minimal governance and enforcement proof of concept for agent-like systems.

It evaluates requested actions, applies deterministic rules, issues capability tokens, enforces permissions, and records decisions in an append-only audit graph.

GateGraph is intentionally small. It is not an autonomous agent, not a platform, not a distributed ledger, and not a full GLP implementation.

---

## What GateGraph does

GateGraph provides:

- deterministic risk classification
- deterministic rule evaluation
- fail-closed decisions
- capability-token-based enforcement
- append-only event logging
- simple graph relations for auditability
- validation simulations for normal use, unusual inputs, and agent scenarios

The core idea:

```text
Task
→ Risk Engine
→ Rule Engine
→ Decision
→ Capability Token
→ Enforcement
→ Audit Event
```

---

## What GateGraph does not do

GateGraph currently does **not** provide:

- autonomous rule changes
- multi-agent orchestration
- runtime/cost control
- production-grade concurrency handling
- token signing
- a distributed ledger
- full GLP protocol compliance

---

## Project status

```text
Version: v0.5 PoC
Core status: stable proof of concept
Production status: not production-ready
```

Current validation summary:

```text
Normal usage simulation:      passed
Unusual input simulation:     passed
Agent scenario simulation:    passed
Unsafe allows:                0
Invariant violations:         0
```

---

## Quickstart

```bash
python tests/test_loop.py
python tests/usage_simulation.py
python tests/unusual_inputs.py
python tests/agent_scenarios.py
```

Depending on your environment, use:

```bash
python3 tests/test_loop.py
```

---

## Repository structure

```text
GateGraph/
├── db/
│   └── schema.sql
├── docs/
│   ├── ARCHITECTURE.md
│   ├── SECURITY.md
│   └── TEST_REPORT.md
├── src/
│   ├── capability_token.py
│   ├── database.py
│   ├── enforcement.py
│   ├── event_logger.py
│   ├── governance.py
│   ├── risk_engine.py
│   └── rule_engine.py
├── tests/
│   ├── agent_scenarios.py
│   ├── test_loop.py
│   ├── unusual_inputs.py
│   └── usage_simulation.py
└── DEVLOG.md
```

---

## Related concepts

GateGraph is inspired by graph-based and append-only audit models, including:

- https://github.com/humancoreai/GLP-Graph-Ledger-Protocol

Important distinction:

- **GLP** focuses on distributed, content-addressed assertion and relation storage.
- **GateGraph** is a deterministic governance and enforcement layer with an audit graph.

GateGraph does **not** implement the GLP protocol. It uses a GLP-inspired local audit graph pattern.

---

## Design principles

- read-only default
- fail closed
- no direct execution without capability token
- untrusted input is data, never instruction
- decisions are deterministic
- events are append-only
- rules are versioned, not silently overwritten

---

## Current next steps

Recommended next work after v0.5:

1. Runtime / cost-control layer for agent loops
2. Pattern Engine for RuleUpdateProposals
3. Token signing / stronger token integrity
4. Concurrency and race-condition handling
5. Query layer for graph traversal


---

## Runtime Guard planning

The next planned layer is documented in:

```text
docs/RUNTIME_GUARD.md
```

Runtime Guard is intentionally separate from GateGraph Core. It handles runtime limits, cost budgets, and loop prevention.
