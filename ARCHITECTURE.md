<!-- v0.9.1_STABLE note: Boundary hardening and release integrity closure; no governance logic expansion. -->

# Architecture – v0.12.0_STABLE

## System role

GateGraph sits before execution. It controls whether a requested action may proceed and under which bounded conditions.

## Core flow

```text
Task
→ Risk Engine
→ Rule Engine
→ Governance Decision
→ Capability Token
→ Enforcement Gate
→ Session Budget Guard
→ Runtime Guard
→ HTTP Policy
→ Secret Resolution
→ Action-ready / Stop
→ Audit / Evidence
```

## Layer separation

### Governance layer

Evaluates deterministic risk/rule inputs and produces a decision. It does not execute actions.

### Enforcement layer

Verifies that execution is authorized by a valid capability token and policy conditions. It is a gatekeeper, not a policy author.

### Runtime/session layer

Applies runtime and budget constraints after enforcement. It does not create new governance policy.

### Audit/evidence layer

Records decisions and evidence for later reconstruction. It supports review and replay, not automatic correction.

### Operator/export layer

Makes recorded state inspectable and exportable. It must remain observational and must not change decisions.

## Release layer

v0.11.4_STABLE adds a release-integrity layer around packaging and review artifacts. This layer verifies structure, hashes and documentation consistency; it does not participate in runtime governance.


## v0.12.0_STABLE Security Mapping Boundary

v0.12.0_STABLE adds security mapping and token exposure hardening only. It does not participate in runtime governance and does not expand authority.


Current release surface: `v0.12.1_STABLE`.


Current release surface: v0.12.7_STABLE.

Current release surface: v0.12.8_STABLE

Release surface: v0.14.7_STABLE.


Release surface: v0.16.0_CANDIDATE.
Base stable: v0.14.7_STABLE.
Phase: Recovery Replay Finality Hardening.
