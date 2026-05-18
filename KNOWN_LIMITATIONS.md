# Known Limitations

## Concurrency / SQLite Ownership

GateGraph currently targets a:

```text
single-node deterministic governance baseline
```

SQLite connections are intentionally treated as thread-owned resources.

Current guarantees:

- deterministic local persistence
- append-only audit behavior
- fail-closed governance behavior
- deterministic runtime evidence generation

Current non-goals:

- distributed runtime execution
- multi-node clustering
- shared cross-thread SQLite handles
- async worker orchestration
- enterprise parallel scaling claims

## Runtime Boundary Clarification

Risk Engine and Rule Engine may be called directly for analysis/testing purposes.

This is expected behavior because they are:

- stateless evaluators
- proposal-generating components
- non-authoritative without Enforcement Layer approval

Authority remains bound to:

```text
Enforcement Layer -> Capability Token -> Runtime Execution
```

Direct evaluator invocation alone does not bypass governance.
