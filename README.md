# GateGraph

GateGraph is a minimal Proof of Concept for a deterministic governance and enforcement layer with an append-only audit graph.

It is designed to answer one practical question:

> Before an agent or tool performs an action, who decided it was allowed, under which rule, with which capability, and where is that decision recorded?

## What GateGraph does

GateGraph implements:

- deterministic risk classification
- deterministic rule evaluation
- append-only event logging
- idempotent event writes
- capability-token based enforcement
- rejection event logging
- a small validation test loop

## What GateGraph is not

GateGraph is not:

- an AGI system
- an autonomous self-learning system
- a full GLP implementation
- a distributed ledger
- a multi-agent runtime

## Architecture

```text
Task
  -> Risk Engine
  -> Rule Engine
  -> Decision
  -> Capability Token
  -> Enforcement Layer
  -> Audit Graph Store
```

The key invariant is simple:

```text
No tool action executes without a valid, non-expired, non-revoked, task-bound capability token.
```

## Related Concepts

GateGraph is inspired by graph-based and append-only data models similar to:

- https://github.com/humancoreai/GLP-Graph-Ledger-Protocol

Clear separation:

- GLP focuses on a distributed, content-addressed ledger for assertions and relations.
- GateGraph is a deterministic governance and enforcement layer with an audit graph.

GateGraph can conceptually sit on top of or alongside GLP-like systems, but it does not implement the GLP protocol.

## Run tests

```bash
python -S tests/test_loop.py
```

Expected current result:

```text
Passed: isolated 20/20 | accumulated 20/20
Failed: 0
Unexpected allows: 0
Invariant violations: 0
```

## Current status

PoC-ready. Not production-ready.

Known production blockers:

- parallel execution / race conditions
- reviewer trust model
- token signing or stronger token integrity
- formal graph query layer
- runtime / cost control layer (intentionally deferred)
