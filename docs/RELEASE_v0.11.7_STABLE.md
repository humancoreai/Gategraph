# Release — GateGraph v0.11.7_STABLE

## Phase

Context / Memory Governance Baseline.

## Claim boundary

GateGraph now treats context as an explicit governance boundary.

This release adds deterministic context classification, required provenance checks, instruction/data separation, replay/explain hardening, and visibility markers for suspicious context patterns.

## Not in scope

- No memory system.
- No vector database.
- No embeddings.
- No semantic scoring.
- No ML classifier.
- No autonomous context filtering.
- No agent memory persistence.
- No AI moderation system.

## Invariants

- Context does not create authority.
- Untrusted context remains data.
- Replay and explain context remains descriptive and non-executable.
- Unknown or inconsistent context provenance fails closed.
- Suspicious content markers are visibility-only.
