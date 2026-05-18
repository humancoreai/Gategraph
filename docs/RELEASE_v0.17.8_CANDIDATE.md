# v0.17.8_CANDIDATE

Base: v0.17.7_STABLE
Status: candidate
Version: 0.17.8
Phase: Concurrency Scope Evidence Formalization

## Scope

Concurrency scope evidence formalization for the existing single-node deterministic governance baseline.

## Included

- explicit SQLite thread-ownership scope statement
- evidence surface for concurrency limitations
- release/documentation hygiene for candidate validation

## Not Included

- no PostgreSQL migration
- no async rewrite
- no distributed or clustered runtime
- no shared SQLite connection across threads
- no new runtime authority
- no new capability scopes

## Promotion Gate

Stable promotion is forbidden until Windows Evidence CI reports `Passed: True` for this candidate.
