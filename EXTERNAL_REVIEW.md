# External Review Baseline

## What GateGraph is

GateGraph is a deterministic governance and enforcement layer for agent-like execution flows. It evaluates requested actions against explicit rules, issues bounded capability tokens, checks enforcement and runtime/session constraints, and records evidence for review.

## What GateGraph is not

GateGraph is not an autonomous agent, not an adaptive AI safety system, not a self-governing policy engine, not a predictive risk model, and not a distributed enterprise platform.

## Review focus

External review should focus on:

- deterministic decision behavior
- fail-closed enforcement boundaries
- separation between governance, enforcement, runtime control and audit
- append-only audit assumptions
- evidence reproducibility
- documentation accuracy
- release/package reproducibility

## Reviewer cautions

Do not infer capabilities from terminology. Explainability means deterministic reconstruction of recorded decisions; it does not mean causal understanding. Pattern and drift components surface evidence and comparisons; they do not automatically change policy.

## Reviewable claim boundary

The reviewable claim for v0.9.0_CANDIDATE is narrow:

> GateGraph is a deterministic, single-node governance/enforcement milestone with auditable evidence and reproducible release packaging.
