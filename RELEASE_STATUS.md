# GateGraph Release Status — v0.8.5 Hygiene Fix

## Status

GateGraph v0.8.5 is a stable single-node proof of concept for deterministic agent-action governance.

This release does not change governance semantics. It only cleans repository hygiene and stabilizes the evidence runner.

## Core invariants

- No action without a valid capability token.
- Enforcement is the only gatekeeper.
- Guards may stop execution, but never grant permission.
- Pattern Engine creates proposals only; it does not mutate rules.
- Audit remains append-only.
- Unknown or invalid states fail closed.

## Validation

Evidence runner command:

```bash
python -S -u tests/evidence_ci.py
```

Validated groups:

- Runtime Stress Evidence
- Session Budget Evidence
- Guard Orchestration Evidence
- Reason Normalization Evidence
- Scale Safety Evidence
- External API Evidence
- Core Loop
- Runtime Guard
- Pattern Engine
- Usage Simulation
- Unusual Inputs
- Agent Scenarios

## Known non-goals

- No distributed budget enforcement.
- No cryptographic token signing.
- No real external APIs.
- No adaptive budget strategy.
- No production-grade billing integration.

## Release note

Generated files such as `__pycache__/`, local SQLite databases and JSON evidence logs are intentionally excluded from the clean release archive.
