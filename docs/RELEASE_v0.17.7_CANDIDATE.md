Release: v0.17.7_CANDIDATE
Base: v0.17.5_STABLE
Status: candidate
Version: 0.17.6
Phase: Evidence Lifecycle Cleanup Formalization

# Release Notes – v0.17.7_CANDIDATE

v0.17.7_CANDIDATE hardens the single-node lifecycle/concurrency surface and formalizes SQLite thread-ownership limitations without changing governance authority, enforcement semantics, token mechanics, policy behavior, or capability scope.

## Scope

- SQLite connection ownership remains thread-local / short-lived.
- Single-node deterministic governance baseline is clarified.
- Direct Risk-/Rule-Engine invocation remains stateless, non-authoritative, and side-effect bounded.
- Simulation findings are updated; outdated Revocation Gap wording is removed.
- Release surface status is candidate until Windows Evidence CI passes.

## Non-Scope

- No PostgreSQL migration.
- No async rewrite.
- No multi-node/cluster runtime.
- No new Runtime Authority.
- No new capability scopes.

## Promotion Gate

Stable promotion is forbidden until this Candidate receives Windows Evidence CI `Passed: True`.

## v0.17.7 Candidate Hardening Addendum

Concurrency / SQLite Ownership Hardening is the operational focus of this candidate.
