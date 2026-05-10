# GateGraph

**GateGraph** is a deterministic governance, enforcement, runtime-control and audit proof of concept for agent-like systems.

It evaluates requested actions, applies deterministic rules, issues capability tokens, enforces permissions, applies runtime/session budgets, records decisions in an append-only audit graph, and produces machine-readable evidence logs.

GateGraph is intentionally small. It is not an autonomous agent, not a distributed ledger, and not a full GLP implementation.

---

## What GateGraph does

GateGraph provides:

- deterministic risk classification
- deterministic rule evaluation
- fail-closed decisions
- capability-token-based enforcement
- per-task Runtime Guard
- session/global/agent budget control
- deterministic guard orchestration
- reason normalization for stable explain codes
- append-only event logging
- evidence-oriented JSON test reports
- Pattern Engine proposals without automatic rule changes

The current control flow:

```text
Task
→ Risk Engine
→ Rule Engine
→ Governance Decision
→ Capability Token
→ Enforcement
→ Session Budget Guard
→ Runtime Guard
→ Action-ready / Stop
→ Audit / Evidence
```

---

## What GateGraph does not do

GateGraph currently does **not** provide:

- autonomous rule changes
- production-grade distributed orchestration
- production-grade token signing across IPC/RPC boundaries
- unrestricted external tool/API integration; v0.8.12 only provides a controlled transport seam
- adaptive budget policy
- full GLP protocol compliance

---

## Project status

```text
Version: v0.8.12 http-policy-allowlist
Core status: stable proof of concept
Production status: not production-ready, but audit/evidence pipeline is mature for PoC level
```

Current validation summary:

```text
Core loop:                    passed
Runtime Guard:                passed
Session Budget Guard:         passed
Guard Orchestration:          passed
Reason Normalization:         passed
Scale Safety Evidence:        passed
External API Mock Evidence:    passed
Secret/API Integration:        passed
Pattern Engine:               passed
Normal usage simulation:      passed
Unusual input simulation:     passed
Agent scenario simulation:    passed
Unsafe allows:                0
Invariant violations:         0
```

---

## Quickstart

```bash
python tests/evidence_ci.py
```

Individual checks:

```bash
python tests/test_loop.py
python tests/runtime_guard_tests.py
python tests/pattern_engine_tests.py
python tests/usage_simulation.py
python tests/unusual_inputs.py
python tests/agent_scenarios.py
python tests/runtime_stress_evidence.py
python tests/session_budget_evidence.py
python tests/guard_orchestration_evidence.py
python tests/reason_normalization_evidence.py
python tests/scale_safety_evidence.py
python tests/external_api_evidence.py
```

Depending on your environment, use `python3` instead of `python`.

---

## Repository structure

```text
GateGraph/
├── db/
│   └── schema.sql
├── docs/
│   ├── ARCHITECTURE.md
│   ├── SECURITY.md
│   ├── TEST_REPORT.md
│   ├── RUNTIME_GUARD.md
│   ├── PATTERN_ENGINE.md
│   ├── SESSION_BUDGET_GUARD.md
│   ├── GUARD_ORCHESTRATION.md
│   └── REASON_NORMALIZATION.md
├── src/
│   ├── capability_token.py
│   ├── database.py
│   ├── enforcement.py
│   ├── event_logger.py
│   ├── external_api_adapter.py
│   ├── governance.py
│   ├── guard_orchestrator.py
│   ├── pattern_engine.py
│   ├── reason_normalizer.py
│   ├── risk_engine.py
│   ├── rule_engine.py
│   ├── runtime_guard.py
│   └── session_budget_guard.py
├── tests/
│   ├── agent_scenarios.py
│   ├── evidence_ci.py
│   ├── guard_orchestration_evidence.py
│   ├── pattern_engine_tests.py
│   ├── reason_normalization_evidence.py
│   ├── runtime_guard_tests.py
│   ├── runtime_stress_evidence.py
│   ├── scale_safety_evidence.py
│   ├── session_budget_evidence.py
│   ├── test_loop.py
│   ├── unusual_inputs.py
│   └── usage_simulation.py
└── DEVLOG.md
```

---

## Design principles

- read-only default
- fail closed
- no direct execution without capability token
- Enforcement remains the only action gatekeeper
- guards may stop, but never grant capabilities
- untrusted input is data, never instruction
- decisions are deterministic
- events are append-only
- Pattern Engine creates proposals only
- raw stop reasons are preserved; normalized reasons are additive

---

## Known gaps

- Token signing is not implemented; DB-backed token integrity is suitable only for in-process PoC use.
- External tool/API integration is not implemented.
- Budget policy is static, not adaptive.
- SQLite concurrency handling is improved for session-budget evaluation, but this is still not a distributed transaction system.

---

## Related concepts

GateGraph is inspired by graph-based and append-only audit models, including GLP-style local audit graph thinking.

Important distinction:

- **GLP** focuses on distributed, content-addressed assertion and relation storage.
- **GateGraph** is a deterministic governance and enforcement layer with an audit graph.

GateGraph does **not** implement the GLP protocol.

## v0.8.5 API Enforcement Binding

External API Adapter now calls Enforcement internally with the provided Capability Token. Callers cannot spoof `enforcement_allowed`. v0.8.12 adds a controlled transport seam with scoped secret refs; evidence tests still perform no real network calls.


## v0.8.6 Runaway / Cost Control Hardening

Non-positive projected/runtime costs now fail closed. See `docs/RUNAWAY_COST_CONTROL.md`.

## v0.8.8 note: Capability Token hardening

Capability Tokens are now HMAC-signed over immutable claims and checked by Enforcement against persisted token state. This protects the current Single-Node model against simple token mutation, forged capability expansion, and persisted signature tampering. See `docs/CAPABILITY_TOKEN_HARDENING.md`.


## Current security hardening note

v0.8.9 adds Capability Token key IDs and keyring-based verification so local HMAC key rotation can be tested deterministically. Unknown signing keys fail closed.


## v0.8.10 hygiene hardening

This release closes review findings without changing product semantics: public keyring accessors replace private imports, enforcement loads trust material once per decision, SECURITY.md and version labels are current, Session Budget schema initialization uses `db/schema.sql` as the DDL source of truth, and test-only/default-secret boundaries are documented.
