Release: v0.17.8_CANDIDATE
Base: v0.17.7_STABLE
Status: candidate
Version: 0.17.8
Phase: Concurrency Scope Evidence Formalization

# Release Notes – v0.17.8_CANDIDATE

Scope: concurrency scope evidence formalization and release-surface hygiene.

## Changes

- Added explicit concurrency scope statement for the single-node SQLite baseline.
- Added evidence that SQLite thread ownership remains documented and non-authoritative.
- Preserved fail-closed, token, boundary, audit and runtime authority invariants.

## Non-goals

- No PostgreSQL migration.
- No async rewrite.
- No multi-node runtime authority.
- No new capability scopes.

## Authority Boundary

- No governance logic change.
- No runtime/enforcement behavior change.
- No autonomous policy update.
- No semantic scoring or memory system.
