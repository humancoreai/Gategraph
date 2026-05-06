# Emergence Boundaries — v0.9.2_STABLE

## Purpose

This document lists forbidden emergence paths for future multi-agent work.

## Forbidden Paths

GateGraph must forbid:

- agent cascades without bounded delegation depth
- recursive delegation drift
- token chaining that broadens capability
- budget farming across child agents
- sibling budget borrowing
- hidden agent-to-agent communication
- unaudited shared scratchpads
- agent-created policy changes
- self-elevation through mode switching
- autonomous human-review bypass
- distributed governance shards
- non-deterministic replay dependencies
- external tool access without HTTP policy and secret gates
- communication channels not represented in audit

## Fail-Closed Principle

Any path that cannot be reconstructed, budgeted, and explained must be blocked before execution.

## Positive Boundary

Multi-agent support is acceptable only when it remains:

- centrally governed
- capability-narrowed
- budget-bounded
- audit-visible
- replay-deterministic
- human-reviewable
