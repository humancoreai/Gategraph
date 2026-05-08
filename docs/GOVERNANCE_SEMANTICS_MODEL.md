# Governance Semantics Model — v0.11.9_CANDIDATE

This document defines semantic boundaries for GateGraph object surfaces. It is descriptive and non-executable.

## Object classes

- `runtime_object`: may participate in runtime guard evaluation only through existing explicit guard paths.
- `reference_object`: descriptive record used for explain, replay, monitoring, archive, export, or review surfaces.
- `proposal_object`: non-authoritative candidate change description.
- `archive_object`: immutable historical record.
- `explain_object`: descriptive trace/snapshot only.

## Invariants

1. Reference objects never create capabilities.
2. Reference objects never mutate policy or governance.
3. Replay and explain objects are never executable context.
4. Proposal objects are not authority.
5. Unknown object classes fail closed.
6. Object promotion is denied unless an explicit trusted governance path already exists.

## Non-goals

No semantic scoring, ML classification, vector memory, autonomous filtering, adaptive trust, or agent memory persistence is introduced.
