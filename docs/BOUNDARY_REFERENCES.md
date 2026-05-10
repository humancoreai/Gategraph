# GateGraph Boundary References

## BOUNDARY-001 – Governance hierarchy

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

Disallowed:

```text
Runtime → Governance
Adapter → Governance Override
Execution → Capability Expansion
```

## BOUNDARY-002 – Multi-agent boundary

```text
External Agent
     ↓ request
Adapter / Caller Boundary
     ↓ normalized request
GateGraph Governance
     ↓ decision + capability
Approved Runtime Action
```

Disallowed:

- implicit delegation,
- autonomous capability expansion,
- hidden agent communication,
- budget authority propagation.

## BOUNDARY-003 – Replay boundary

```text
Event Creation
    ↓
Append-Only Audit
    ↓
Replay Pipeline
    ↓
Deterministic Reconstruction
```

Disallowed:

- event mutation,
- silent event deletion,
- replay rewriting,
- adapter-side replay substitution.

## BOUNDARY-004 – Adapter boundary

```text
External Tool / Agent
        ↓
Adapter
        ↓
GateGraph
        ↓
Approved Action
```

Adapters may translate and forward requests. They may not authorize, escalate, override, mutate replay, or create capabilities.
