# MAX Simulation Findings – v0.17.9_CANDIDATE

## Confirmed PASS Areas

- Token forgery blocked
- Boundary matrix stable
- Revocation checks PASS
- Append-only audit stable
- Budget cascade behavior stable
- Fail-closed enforcement stable

## Primary Finding

Observed instability source:

```text
SQLite thread ownership / parallel connection handling
```

This is currently treated as a controlled single-node limitation rather than a governance failure.

## Clarification

Previous simulation comments referencing:

```text
Revocation Gap
```

are outdated and no longer reflect the current runtime state.

Revocation validation is currently PASS in simulation evidence.
