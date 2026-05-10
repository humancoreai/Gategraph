# Context Lifecycle Model — GateGraph v0.12.0_STABLE

## Purpose

This release tightens the lifecycle view around the v0.11.7 context governance boundary.

The lifecycle model is not a memory system. It does not persist agent memory, rank context, score meaning, infer intent, or decide whether content is true. It only makes context movement explicit enough to block hidden authority promotion paths.

## Lifecycle states

Supported descriptive states: `received`, `classified`, `bounded`, `referenced`, `archived`, `replayed`, `expired`.

Unknown lifecycle states fail closed.

## Allowed transitions

Allowed transitions are intentionally narrow: `received` → `classified`, `classified` → `bounded`, `bounded` → `referenced`, `referenced` → `archived`, `archived` → `replayed`, `replayed` → `referenced`, `referenced` → `expired`, and `archived` → `expired`.

All other transitions fail closed.

## Non-authority rule

Lifecycle movement does not mutate provenance. It must not create a capability, grant execution authority, change trust level, convert replay/explain/proposal context into runtime context, alter governance influence, or rehydrate archived/replayed context into a trusted instruction source.

## Replay and explain semantics

Replay/explain material remains reference-only. A replayed context may be observed and referenced, but it must not become executable context or policy input by being replayed.

## Boundary of this release

No memory system, vector database, embeddings, semantic scoring, ML classifier, autonomous context filtering, adaptive trust system, AI moderation, long-term agent memory, new runtime capability, or adapter authority is introduced.
