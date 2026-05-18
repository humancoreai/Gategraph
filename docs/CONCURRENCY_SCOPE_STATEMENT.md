# Concurrency Scope Statement

Release: v0.17.9_STABLE
Base: v0.17.8_STABLE
Status: stable
Phase: Concurrency Scope Evidence Formalization

GateGraph currently defines a single-node deterministic governance baseline. SQLite persistence is treated as thread-owned.

## Guaranteed Scope

- deterministic local evidence generation
- conservative SQLite connection ownership
- no intentional cross-thread connection reuse
- fail-closed governance behavior preserved
- append-only audit semantics preserved

## Explicit Non-Scope

- distributed runtime execution
- multi-node clustering
- shared SQLite handles across threads
- async worker orchestration
- enterprise parallel scaling claims

## Authority Boundary

This document is descriptive only. It does not add runtime authority, policy mutation, capability scopes, or enforcement behavior.
