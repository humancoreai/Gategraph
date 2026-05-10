# Runtime Boundary Hardening – v0.10.0_CANDIDATE

## Scope

v0.10.0_CANDIDATE hardens existing runtime entry assumptions without adding new runtime capabilities, adapters, agent behavior, or orchestration paths.

## Boundary rule

Governance evaluation requires an explicit `trusted_entry_context`.

Allowed production path:

```text
public request -> service_adapter -> governance
```

Forbidden production path:

```text
external caller -> governance.evaluate_task()
```

## Enforcement

`src/runtime_path_assertions.py` defines the trusted entry context and fail-closed validation.

`src/governance.py` calls `assert_trusted_entry_context()` before risk classification, rule evaluation, audit logging, budget reservation, or token issuance.

`src/service_adapter.py` creates the production trusted context only after caller boundary metadata has been validated.

## Test compatibility

Historical evidence scripts that call Governance directly use a test-only compatibility path through `GATEGRAPH_ALLOW_TEST_DIRECT_GOVERNANCE=1` set by the evidence runner.

This is not a production path and is verified separately by `tests/runtime_boundary_hardening_evidence.py`, which removes the compatibility flag and proves naked direct Governance invocation fails closed.

## Non-scope

This phase does not add:

- new agents
- new adapters
- new orchestration
- new risk model
- new runtime execution model
- framework integration
- HTTP auth/TLS
- packaging/deployment changes
