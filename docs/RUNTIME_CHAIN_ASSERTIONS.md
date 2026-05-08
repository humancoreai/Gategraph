# Runtime Chain Assertions – v0.11.3_STABLE

## Scope

This document defines the executable guard-chain invariant introduced in v0.11.3_STABLE.

It is a hardening step only. It does not introduce new runtime capability, new adapters, new agent behavior, packaging, deployment, UI, or orchestration.

## Required chain

A runtime action may only become `action_ready` after the following ordered prefix has been evaluated:

1. `enforcement`
2. `flood_guard`
3. `session_budget`
4. `runtime_guard`
5. `action_ready`

## Fail-closed cases

The runtime chain assertion must fail closed for:

- missing `enforcement` as first stage
- skipped intermediate stages
- duplicate stage evaluation
- unknown stages
- `action_ready` without the full chain
- downstream guard evaluation after enforcement denied
- terminal stage mismatch

## Invariant mapping

This strengthens the v0.9.3 freeze baseline by making selected boundary/order claims executable:

- Governance and Enforcement remain separate.
- Enforcement is the first runtime gate.
- Runtime guards cannot grant authority.
- A ready action requires a complete ordered guard chain.
- Invalid or ambiguous runtime chains fail closed.
