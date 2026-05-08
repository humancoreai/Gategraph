# Governance Surface Freeze

## Scope

`v0.12.0_STABLE` introduces descriptive surface contracts for core GateGraph outputs and review surfaces.

The contracts define stable field shapes for:

- governance decisions
- normalized reasons
- monitoring exports
- capability token claims

## Invariant

Contracts are review and compatibility artifacts only. They do not execute policy, authorize actions, mutate governance state, resolve secrets, or change runtime/enforcement behavior.

## Boundary

Surface contracts may be used by evidence tests and reviewers to detect drift. They must not become a second source of governance authority.

## Non-scope

- no autonomous governance adaptation
- no semantic scoring
- no memory system
- no LLM-based enforcement
- no runtime authority expansion
- no external schema validator dependency

## Promotion requirement

Candidate promotion requires surface contract evidence, semantic boundary evidence, version consistency evidence, release process guard evidence and full Evidence CI to pass.
