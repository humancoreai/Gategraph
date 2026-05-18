Release: v0.17.7_STABLE
Base: v0.17.6_STABLE
Status: stable
Version: 0.17.7
Phase: Evidence Lifecycle Cleanup Formalization

# Release Notes – v0.17.7_STABLE

v0.17.7_STABLE finalizes the single-node lifecycle/concurrency hardening surface and formalizes SQLite thread-ownership limitations without changing governance authority, enforcement semantics, token mechanics, policy behavior, or capability scope.

## Scope

- SQLite connection ownership remains thread-local / short-lived.
- Single-node deterministic governance baseline is clarified.
- Direct Risk-/Rule-Engine invocation remains stateless, non-authoritative, and side-effect bounded.
- Simulation findings are updated; outdated Revocation Gap wording is removed.
- Release surface status is stable after Windows Evidence CI passed for the candidate.

## Non-Scope

- No PostgreSQL migration.
- No async rewrite.
- No multi-node/cluster runtime.
- No new Runtime Authority.
- No new capability scopes.

## Promotion Gate

Stable promotion completed after v0.17.7_CANDIDATE received Windows Evidence CI `Passed: True`.

## v0.17.7 Stable Hardening Addendum

Concurrency / SQLite Ownership Hardening is the operational focus of this candidate.


## CI Evidence

Windows Evidence CI for v0.17.7_CANDIDATE: `Passed: True` (user-provided report, 2026-05-18).
