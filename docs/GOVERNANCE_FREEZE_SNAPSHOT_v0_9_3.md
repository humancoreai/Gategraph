# GateGraph Governance Freeze Snapshot – v0.9.3_STABLE

## Purpose

This snapshot defines the audit baseline for GateGraph after v0.9.2_STABLE. It captures the stable governance boundaries, invariant IDs, and review assumptions used to assess later changes.

This document is descriptive and constraining. It does not introduce runtime behavior.

## Snapshot metadata

| Field | Value |
|---|---|
| Version | v0.9.3_STABLE |
| Base | v0.9.2_STABLE |
| Snapshot type | Governance freeze / audit baseline |
| Runtime scope | Single-node governance runtime |
| Autonomy added | No |
| Distributed governance added | No |
| Adapter execution added | No |

## Core guarantees

- Governance decisions remain centralized.
- Enforcement remains mandatory.
- Runtime guards do not override governance decisions.
- Audit history remains append-only.
- Replay remains deterministic.
- Fail-closed behavior remains the default under uncertainty.
- Adapter and multi-agent boundaries do not grant implicit authority.

## Non-goals

GateGraph does not provide:

- autonomous planning,
- emergent delegation,
- distributed governance,
- self-modification,
- autonomous tool orchestration,
- autonomous capability creation,
- adapter-side governance.

## Authority hierarchy

```text
Human Authority
       ↓
Governance Layer
       ↓
Enforcement Layer
       ↓
Runtime Layer
       ↓
Approved Execution
```

Forbidden authority flows:

```text
Runtime → Governance
Adapter → Governance Override
Execution → Capability Expansion
```

## Referenced documents

- `docs/INVARIANT_REGISTRY.md`
- `docs/BOUNDARY_REFERENCES.md`
- `docs/THREAT_MODEL.md`
- `docs/MULTI_AGENT_SSOT.md`
- `docs/MULTI_MODE_SSOT.md`
- `docs/DELEGATION_BOUNDARY.md`
- `docs/MULTI_AGENT_REPLAY_AUDIT.md`
- `docs/RELEASE_REPRODUCIBILITY.md`

## Freeze rule

Any future change touching enforcement order, capability validation, runtime guards, budget authority, audit semantics, replay semantics, adapter authority, or delegation must be checked against the invariant registry before release.
