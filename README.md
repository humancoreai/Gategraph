# GateGraph

Current candidate: **v0.9.0_CANDIDATE**

GateGraph is a deterministic governance, enforcement, runtime-control and audit proof-of-concept for agent-like systems. It evaluates requested actions, applies deterministic rules, issues capability tokens, enforces permissions, applies runtime/session budgets, records decisions in an append-only audit trail, and produces evidence logs for review.

GateGraph is intentionally bounded. It is not an autonomous agent, not a self-governing system, not an adaptive AI safety layer, not a predictive risk model, and not a full GLP implementation.

## v0.9.0 milestone purpose

v0.9.0_CANDIDATE is a release and external-review baseline. It consolidates the v0.8.x line by adding review documents, scope-freeze documents, deterministic release packaging and milestone consistency evidence. It does not add new governance decision logic.

## Core flow

```text
Task
→ Risk Engine
→ Rule Engine
→ Governance Decision
→ Capability Token
→ Enforcement
→ Session Budget Guard
→ Runtime Guard
→ HTTP Policy
→ Secret Resolution
→ Action-ready / Stop
→ Audit / Evidence
```

## What GateGraph provides

- deterministic risk/rule evaluation
- fail-closed decisions
- capability-token-based enforcement
- runtime and session budget controls
- deterministic guard orchestration
- reason normalization for stable explain codes
- append-only audit/evidence orientation
- replay, archive, drift and operator export evidence
- local/protected server adapter for evaluate/status/monitoring integration
- deterministic release packaging for external review

## What GateGraph does not provide

See [`NON_SCOPE.md`](./NON_SCOPE.md). In short: no autonomous rule changes, no self-governance, no automatic optimization, no ML/prediction layer, no multi-node governance, no production enterprise deployment claim.

## Review documents

- [`EXTERNAL_REVIEW.md`](./EXTERNAL_REVIEW.md)
- [`ARCHITECTURE.md`](./ARCHITECTURE.md)
- [`INVARIANTS.md`](./INVARIANTS.md)
- [`NON_SCOPE.md`](./NON_SCOPE.md)
- [`RELEASE_CONTENT_RULES.md`](./RELEASE_CONTENT_RULES.md)

## Packaging

Use:

```bash
python tools/build_release.py
python tools/verify_release.py dist/GateGraph_v0.9.0_CANDIDATE.zip
```

The release ZIP is built with sorted entries, fixed ZIP timestamps, hidden-file exclusion and SHA256 verification data.
