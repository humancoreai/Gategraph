# Release Status

Current stable: **v0.8.33_STABLE**

Base stable: **v0.8.32_STABLE**

## Stable scope

Phase 2 server/integration layer:

- minimal HTTP adapter
- shared CLI/server service adapter
- `POST /evaluate`
- `GET /status`
- `GET /monitoring`
- server evidence test
- CLI fail-closed mode boundary

## Stable gate

Passed.

Target-environment Windows Evidence CI:

```text
CI EVIDENCE REPORT
Passed: True
```

## Stable invariants

- Server Mode remains adapter-only.
- CLI and Server use the shared `service_adapter` path.
- Unsupported CLI modes fail closed with non-zero exit code.
- Monitoring export remains read-only.
- No Governance Core, Runtime Guard, Budget Ledger, HTTP Policy, Secret Handling, or Operational decision logic was changed for the Stable promotion.
