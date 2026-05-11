# Governance Integrity Graph — v0.12.8_STABLE

Base: v0.14.7_STABLE

This release adds a deterministic, declarative relationship map for governance artifacts.

The graph is descriptive only. It does not add runtime authority, policy mutation, auto-repair, self-healing, dynamic loading, distributed consensus, or execution behavior.

Canonical edge types:

- `depends_on`
- `validated_by`
- `affects`
- `lineage_of`

Purpose:

- make registry/evidence/freeze/replay relationships visible
- detect orphaned governance artifacts
- show impact of declarative changes
- support deterministic governance diffs
- keep promotion and release-state surfaces auditable

Non-scope:

- no automatic governance repair
- no runtime graph interpretation
- no graph-based authorization
- no policy learning
- no semantic scoring
