# GateGraph Invariants

## Decision invariants

- Governance decisions are deterministic for the same input and policy state.
- Unknown, malformed or unverifiable inputs fail closed.
- Capability tokens are bounded to their intended task/action context.
- Enforcement must occur before runtime/session execution checks.

## Authority invariants

- GateGraph does not create goals.
- GateGraph does not autonomously change policy.
- Pattern, drift, replay and export layers are evidence/inspection layers unless explicitly implemented otherwise in a later scoped phase.
- Operator-facing outputs must not introduce implicit prioritization or automatic action recommendations.

## Audit invariants

- Audit/event history is append-only.
- Replay and archive checks verify consistency; they do not rewrite history.
- Explanation outputs reconstruct recorded decision structure; they must not claim causal certainty beyond recorded evidence.

## Release invariants

- Release packaging must be deterministic.
- Release artifacts must have a manifest and SHA256 integrity data.
- Source releases must exclude generated runtime artifacts and hidden files.
- Documentation must not claim capabilities outside implemented behavior.
