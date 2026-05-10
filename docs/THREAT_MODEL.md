# Threat Model – v0.9.3_STABLE

## Scope

This document is the referenced threat-model baseline for the v0.9.3_STABLE governance freeze snapshot.

It is documentation-only and introduces no runtime behavior, adapter behavior, orchestration logic, governance logic, or enforcement logic.

## Protected properties

GateGraph protects the following release-critical properties:

- governance decisions remain centralized
- enforcement remains mandatory before execution
- capability tokens remain task-bound and signed
- runtime guards cannot override governance decisions
- audit history remains append-only
- replay assumptions remain deterministic
- adapter and multi-agent boundaries do not create implicit authority

## Primary threat classes

### Authority bypass

Risk: execution, adapter, runtime, or agent-side code obtains authority without Governance and Enforcement approval.

Expected control:
- mandatory enforcement gate
- signed capability token validation
- fail-closed behavior under missing, invalid, or ambiguous authority

### Runtime escalation

Risk: runtime guards, budget guards, or execution loops silently expand task capability.

Expected control:
- runtime guards constrain execution only
- runtime components do not create governance decisions
- loop, step, and budget constraints remain bounded

### Audit or replay drift

Risk: release documentation, audit assumptions, replay artifacts, and tests describe inconsistent baselines.

Expected control:
- invariant registry
- boundary references
- release integrity evidence
- deterministic release manifest
- stable metadata consistency

### Secret or external API misuse

Risk: secrets or external endpoints are used outside approved scope.

Expected control:
- secret references only
- resolution after governance/enforcement approval
- HTTP allowlist and method/path constraints
- fail-closed behavior on policy mismatch

### Multi-agent boundary confusion

Risk: multiple agents are interpreted as distributed governance or implicit delegation authority.

Expected control:
- multi-agent boundary remains descriptive and constrained
- no distributed governance
- no autonomous self-orchestration
- no adapter-side governance authority

## Non-goals

This threat model does not claim:

- internet-facing production hardening
- distributed consensus security
- autonomous agent safety
- cryptographic supply-chain signing
- formal verification
- sandbox escape prevention

## Stable freeze statement

v0.9.3_STABLE treats this threat model as a release-boundary reference. Future changes that alter authority, enforcement order, replay semantics, audit semantics, adapter authority, secret resolution, or multi-agent boundaries must be reviewed against this document and the invariant registry.


See also `docs/DEPLOYMENT_BOUNDARY.md` for the supported/unsupported/unsafe deployment surface introduced in v0.11.0_STABLE.
