# Release Notes — v0.17.9_CANDIDATE

Release: v0.17.9_CANDIDATE
Base: v0.17.8_STABLE
Status: candidate
Phase: Concurrency Scope Evidence Formalization

## Scope

- Development keyring no longer loads silently.
- Local evidence explicitly opts into `GATEGRAPH_ALLOW_DEV_KEYRING=1`.
- Server `/evaluate`, `/status`, and `/monitoring` share the single-node DB boundary lock.
- Enforcement token validation uses a local SQLite `BEGIN IMMEDIATE` section when it owns the transaction.
- Evidence profile organization is documented without pruning tests.
- Release surfaces are repaired without global token replacement.

## Non-Scope

- No PostgreSQL migration.
- No multi-node runtime.
- No new runtime authority.
- No capability-scope expansion.

No governance logic change.
No runtime/enforcement behavior change.
No autonomous policy update.
No semantic scoring or memory system.
