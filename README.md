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
- Pattern Engine proposals from repeated audit patterns with advisory priority/score metadata and without automatic rule changes

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
→ HTTP Policy
→ Secret Resolution
→ Action-ready / Stop
→ Audit / Evidence
```

---

## What GateGraph does not do

GateGraph currently does **not** provide:

- autonomous rule changes
- production-grade distributed orchestration
- production-grade token signing across IPC/RPC/distributed trust boundaries
- unrestricted external tool/API integration; current releases only provide a controlled policy-gated transport seam
- production secret management / KMS / OS-keychain lifecycle
- adaptive budget policy
- full GLP protocol compliance

---

## Governance

GateGraph governance principles are documented in [GOVERNANCE.md](./GOVERNANCE.md).

---

## Project status

Current stable release: **v0.8.29_STABLE**

This stable release adds read-only Operational Alerting on top of existing append-only operational incidents. Alerts are signals only; they do not repair, unblock, acknowledge, resolve, or mutate governance state.


```text
Version: v0.8.29_STABLE
Base: v0.8.28_STABLE
Core status: stable proof of concept; operational alerting stable
Production status: not production-ready; monitoring transport, recovery, and distributed layers remain out of scope
```

Current validation summary:

```text
Full Windows Evidence CI:       passed
Core loop:                      passed
Runtime Guard:                  passed
Session Budget Guard:           passed
Guard Orchestration:            passed
Reason Normalization:           passed
Scale Safety Evidence:          passed
Cross-Session Budget Evidence:  passed
Operational Hardening:          passed
Operational Alerting:           passed
Evidence Runner Selftest:       passed
External API Mock Evidence:     passed
Secret/API Integration:         passed
Pattern Engine:                 passed
Pattern Intelligence:           passed
Normal usage simulation:        passed
Unusual input simulation:       passed
Agent scenario simulation:      passed
Unsafe allows:                  0
Invariant violations:           0
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
python tests/pattern_intelligence_evidence.py
python tests/usage_simulation.py
python tests/unusual_inputs.py
python tests/agent_scenarios.py
python tests/runtime_stress_evidence.py
python tests/session_budget_evidence.py
python tests/guard_orchestration_evidence.py
python tests/reason_normalization_evidence.py
python tests/scale_safety_evidence.py
python tests/external_api_evidence.py
python tests/operational_hardening_evidence.py
python tests/operational_alerting_evidence.py
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
│   ├── OPERATIONAL_ALERTING.md
│   ├── CROSS_SESSION_BUDGET_CONTROL.md
│   ├── GUARD_ORCHESTRATION.md
│   └── REASON_NORMALIZATION.md
├── src/
│   ├── budget_ledger.py
│   ├── capability_token.py
│   ├── database.py
│   ├── enforcement.py
│   ├── event_logger.py
│   ├── external_api_adapter.py
│   ├── governance.py
│   ├── guard_orchestrator.py
│   ├── operational_hardening.py
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
│   ├── operational_alerting_evidence.py
│   ├── pattern_engine_tests.py
│   ├── reason_normalization_evidence.py
│   ├── runtime_guard_tests.py
│   ├── runtime_stress_evidence.py
│   ├── cross_session_budget_evidence.py
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

## Known gaps / what GateGraph cannot do yet

GateGraph is currently a Single-Node PoC. It does **not** yet provide:

- production-grade secret management (no KMS, no OS-keychain lifecycle, no automated rotation)
- distributed trust, asymmetric signatures, or cross-node token verification
- real unrestricted HTTP/API execution; only a controlled transport seam with allowlisted endpoint policies
- production billing integration, customer-level quota enforcement, or alert delivery
- multi-node/distributed budget coordination
- sandboxed tool runtime or operating-system isolation
- human approval workflow / reviewer trust model
- adaptive budget strategy or autonomous rule updates
- final public trace API contract; `explain_trace.py` is reviewer-facing PoC evidence

Implemented at PoC level:

- HMAC-signed, task-bound Capability Tokens with key IDs and local keyring verification
- runtime/session/agent budget guards for loop, step, and cost controls
- HTTP allowlist policy for scheme/host/path/method
- env-backed secret references with no raw secret values in SQLite or audit traces
- append-only audit evidence and read-only explain trace reconstruction
- read-only operational alert signals from append-only incident records

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


## v0.8.14 Security Finesse

Block B hardens edge-case confidence without adding new product scope:
- secret values are verified absent from audit/evidence outputs,
- HTTP policy denial is proven to happen before secret resolution,
- subdomains and wildcard hosts are not implicitly allowed,
- path-prefix matching is boundary-aware (`/v1` does not allow `/v10`),
- combined expired+revoked tokens remain fail-closed.


## v0.8.16 Audit/Explain Reconstruction Evidence

Block D adds a read-only reviewer trace builder and evidence scenarios proving that completed, blocked, HTTP-policy, and secret-backed flows can be reconstructed from persisted audit evidence. Production governance/enforcement/runtime semantics are unchanged.


## v0.8.17 Block E documentation reality check

This release aligns README, SECURITY notes, release status, and current limitations with the actual v0.8.16 system state. It makes no production logic changes.


## v0.8.19 Pattern priority scoring

Pattern proposals now include advisory priority and score metadata for human triage. The Pattern Engine remains strictly proposal-only and cannot change rules, policies, budgets, tokens, secrets, or actions.


## Controlled Apply v0.8.22

GateGraph now includes a strictly limited Controlled Apply prototype. It is disabled by process unless a proposal has first passed manual review and then receives two distinct controlled-apply approvals. Initial scope is rule hardening only; unsupported or loosening changes fail closed. See `docs/CONTROLLED_APPLY.md`.


## v0.8.26 Cross-Session Budget Control

This stable release adds a single-node Budget Ledger and token-bound budget reservations to prevent task/session splitting from bypassing budget controls. Runtime remains non-authoritative; Governance reserves budget and Enforcement verifies the signed/persisted budget claims. See `docs/CROSS_SESSION_BUDGET_CONTROL.md` and `docs/RELEASE_v0.8.27.1_STABLE.md`.

## v0.8.27.1 Stable Operational Hardening

This stable release adds operational visibility and consistency checks without changing the authority model. Budget snapshots, deterministic audit replay checks and append-only incident records are now part of the stable scope. The POSIX Evidence Runner timeout path was hardened by replacing the external `timeout` wrapper with Python-owned process supervision. Full Windows Evidence CI reported `Passed: True` on 2026-04-28.

## Single-Node CLI (v0.8.32_CANDIDATE)

GateGraph can be operated locally through a minimal CLI adapter.

Initialize a local database:

```bash
python -m src.cli --config config.example.yaml init --reset
```

Evaluate a task:

```bash
python -m src.cli --config config.example.yaml evaluate --task task.example.json --token-out token.out.json
```

Export monitoring state:

```bash
python -m src.cli --config config.example.yaml export-monitoring --out monitoring.json
```

Show local status:

```bash
python -m src.cli --config config.example.yaml status
```

The CLI is an adapter only. Governance, Enforcement, Budget, Runtime and Operational logic remain unchanged.
