# Recovery & Replay Hardening

v0.12.7_STABLE hardens the descriptive recovery/replay foundation without adding repair authority.

## Scope

- duplicate recovery attempts are visible and idempotent
- reservation recovery collisions fail closed
- partial-state recovery remains descriptive and fail-closed
- recovery sequences are represented as append-only audit events
- replay order is deterministic and explicit-sequence aware
- replay, explain, archive and recovery objects remain reference-only
- release, manifest, freeze and recovery surfaces remain synchronized

## Non-scope

- no automatic repair loop
- no policy mutation
- no runtime authority expansion
- no distributed recovery protocol
- no production self-healing
- no replay execution
- no runtime rehydration from replay or recovery objects

## Invariant

Recovery evidence may describe, classify, release an interrupted local reservation through an explicit bounded effect, or reject state. It must not invent missing authority, recreate capability tokens, mutate governance rules, or promote replay/explain/archive/recovery objects into runtime input.

Current release surface: v0.12.8_STABLE

Release surface: v0.14.7_STABLE.

Release surface: v0.14.10_STABLE.
Base stable: v0.14.7_STABLE.
Phase: Recovery Replay Finality Hardening.
