# PRODUCTION.md

GateGraph v0.8.32_STABLE is production-ready for the defined single-node scope.

## Scope

- Single-node operation
- CLI evaluation
- Read-only monitoring export
- Deterministic governance and enforcement

## Out of scope

- Server mode
- Distributed budget coordination
- External monitoring integration
- Automated recovery

## Responsibility model

- Human: final decision authority
- Governance: rule enforcement
- Runtime: execution only
- Operational layer: read-only observation
- CLI/Server adapters: no independent decision logic
