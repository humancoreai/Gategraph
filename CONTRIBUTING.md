# Contributing to GateGraph

GateGraph contributions must preserve deterministic governance boundaries.

## Scope Rules

Accepted changes must fit the current release scope. Feature expansion, new runtime models, adaptive governance, ML classification, and implicit prioritization are not allowed unless explicitly opened in a future scoped phase.

## Governance Rules

- Governance decision logic must remain centralized.
- Enforcement must remain separate from decision generation.
- Audit history must remain append-only.
- Pattern or review systems may propose only; they must not auto-apply policy changes.
- Caller-trust boundary assumptions must be documented and tested.

## Evidence Requirements

Every behavior change must include evidence coverage. Evidence must be deterministic, bounded, and runnable through the project evidence CI.

## Determinism Requirements

- No time-dependent release artifacts except explicitly normalized timestamps.
- No unordered file discovery in release packaging.
- No hidden defaults for security-critical metadata.
- No silent repair of malformed release or request state.

## Documentation Requirements

Documentation must not claim more than the code verifies. Security, governance, and release claims must be testable or explicitly marked as assumptions/non-goals.
