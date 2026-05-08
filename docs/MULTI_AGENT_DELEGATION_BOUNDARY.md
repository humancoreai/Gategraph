# Multi-Agent Delegation Boundary

Release: v0.11.7_STABLE  
Base: v0.11.7_STABLE

## Scope

This release documents and tests delegation boundaries for multi-agent scenarios. It does not add agent execution, new runtime modes, new policy authority, distributed orchestration, or automatic governance changes.

## Boundary rules

- Delegation is reference-only unless a separate human review path explicitly evaluates it.
- Delegation never transfers capability tokens.
- Delegation never expands budgets.
- Delegation never grants transitive authority.
- Actor-chain attribution is mandatory.
- Circular delegation fails closed.
- Capability amplification through delegation fails closed.
- Unsupported delegation modes fail closed.

## Allowed evidence-only labels

- `reference_only`
- `proposal_only`
- `human_review_required`

These labels are descriptive. They do not create execution rights.

## Explicit non-goals

- No multi-node orchestration.
- No autonomous agent spawning.
- No hidden worker privileges.
- No adapter-side governance decisions.
- No delegated secret access.
- No budget inheritance.
- No policy mutation.

## Evidence

`tests/multi_agent_delegation_boundary_evidence.py` verifies single reference delegation, transitive authority blocking, circular delegation blocking, capability amplification blocking, actor-chain fail-closed behavior, unsupported mode fail-closed behavior, and authority-free summaries.
