# Architecture – GateGraph v0.12.0_STABLE

# GateGraph Architecture

## 1. Overview

GateGraph is a deterministic governance core with a local append-only audit graph.

It is composed of five conceptual layers:

```text
Client / Agent
→ Governance Layer
→ Capability Enforcement Layer
→ Tool / Runtime Layer
→ Audit Graph Store
→ Pattern Engine (future)
```

The current PoC implements the first four layers and a local audit store.

---

## 2. Core layers

### 2.1 Governance Layer

The Governance Layer is the only entry point for action evaluation.

It coordinates:

- Risk Engine
- Rule Engine
- Decision generation
- Event logging
- Capability Token issuance

Invariant:

```text
Callers do not invoke Risk Engine, Rule Engine, or Event Logger directly.
```

---

### 2.2 Risk Engine

The Risk Engine classifies requests into:

```text
low
medium
high
critical
```

Current priority order:

```text
1. secrets_involved → critical
2. data_sensitivity == secret → critical
3. unknown input_source/data_sensitivity → medium
4. write/delete/modify_config → high
5. api_call + external → medium
6. untrusted input → medium
7. otherwise → low
```

This is intentionally deterministic and stateless.

---

### 2.3 Rule Engine

The Rule Engine evaluates active rules and selects one final decision.

Decision types:

```text
allow
warn
require_review
require_approval
block
```

Canonical ordering:

```text
1. severity_rank DESC
2. decision_rank DESC
3. priority DESC
4. rule_id ASC
```

No matching rule results in a fail-closed `block`.

---

### 2.4 Capability Enforcement Layer

The Enforcement Layer is the hard boundary between a decision and an action.

It validates:

- token exists
- token belongs to the same task
- token is not expired
- token is not revoked
- requested capability is explicitly allowed

Invariant:

```text
No action executes without a valid capability token.
```

---

### 2.5 Audit Graph Store

The Audit Graph Store records events and relations.

It is:

- append-only
- local SQLite in the PoC
- not an authority
- not a decision-maker

Events include:

- schema version
- idempotency key
- correlation ID
- causation ID
- actor metadata
- input snapshot
- evaluation snapshot
- decision snapshot

Relations model simple graph edges:

```text
Task → generated → Event
Event → matched → Rule
Event → produced → Decision
Event → issued → CapabilityToken
```

---

## 3. Runtime flow

```text
1. Task comes in
2. Governance creates correlation/idempotency context
3. Risk Engine classifies risk
4. Rule Engine evaluates active rules
5. Governance builds final capability map
6. Decision is logged as event
7. Decision record is stored
8. Relations are written
9. Capability Token is issued if at least one capability is allowed
10. Enforcement validates token before action
11. Rejections are logged as events
```

---

## 4. Current implemented semantics

### allow / warn

May issue tokens for explicitly requested capabilities.

### require_review

Issues an analysis-only token for `read_files`.

It does not allow:

```text
write_files
delete_files
api_call
unknown tools
```

### require_approval / block

No action token is issued.

---

## 5. Current known limits

- no real human approval workflow yet
- no runtime/cost control layer yet
- no token signing
- no production concurrency model
- no formal graph query layer
- no autonomous rule updates

These are intentionally outside the v0.5 PoC scope.


## v0.12.0_STABLE Security Mapping Boundary

v0.12.0_STABLE adds security mapping and token exposure hardening only. It does not participate in runtime governance and does not expand authority.


Current release surface: `v0.12.1_STABLE`.


Current release surface: v0.12.4_STABLE.

Current release surface: v0.12.7_STABLE


Release surface: v0.17.6_STABLE.

Release surface: v0.17.6_STABLE.


Release surface: v0.17.6_STABLE.
Base stable: v0.14.7_STABLE.
Phase: Recovery Replay Finality Hardening.
