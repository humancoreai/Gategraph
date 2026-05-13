# Semantic Boundary Preparation

Status: observability-only / proposal-only.

This surface records uncertainty markers, unverifiable states and interpretation-boundary placeholders for later review.

Invariant: these markers have no enforcement authority, no runtime authority, no policy mutation authority and no semantic scoring effect.

Allowed marker classes:

- `uncertainty_marker`
- `unverifiable_state`
- `interpretation_boundary_placeholder`
- `proposal_only_semantic_signal`

Forbidden behavior:

- automatic policy update
- automatic mitigation
- runtime decision change
- enforcement decision change
- LLM-based governance decision
