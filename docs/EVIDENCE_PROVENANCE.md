# Evidence Provenance

Release: v0.12.7_STABLE

Base: v0.12.6_STABLE

This document describes deterministic, read-only provenance for evidence files, governance-lineage snapshots, dependency visibility, mutation visibility and replay provenance.

## Invariants

- Provenance is descriptive only.
- Provenance does not grant runtime authority.
- Provenance does not mutate policy, registry, schema, freeze, replay or enforcement state.
- Dependency visibility is read-only and deterministic.
- Replay provenance reconstructs the declared governance state; it does not execute it.

## Non-scope

- No distributed consensus.
- No dynamic plugin loading.
- No auto-repair.
- No auto-migration.
- No self-modifying registry.
