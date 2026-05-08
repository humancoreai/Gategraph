# Runtime Boundary Hardening – v0.10.1_CANDIDATE

## Purpose

Runtime boundary hardening turns entry-path assumptions into executable checks. It does not add new runtime capability, adapter behavior, agent behavior, or orchestration logic.

## Public entry

The only supported public evaluation entry is:

`public_api -> service_adapter -> governance`

The service adapter validates caller boundary metadata and constructs the trusted entry context before Governance is called.

## Internal components

Governance, runtime guards, session budget guards, and enforcement are internal implementation components. They are not public entry points and must not be exposed directly by future integrations.

## Forbidden entry paths

The following components/classes of callers are forbidden from direct Governance entry:

- external plugins
- framework adapters
- agent runtimes
- operator UI surfaces
- unknown components

They must pass through a declared public boundary that performs caller-boundary validation.

## Test-only path

A direct test-harness path exists only for isolated legacy evidence scripts and is environment-gated. It is not a production or public API path.

## Freeze-aware runtime evidence

Selected freeze assumptions are now tied to executable checks:

- naked Governance calls fail closed by default
- only the service adapter can act as public evaluation entry
- forbidden components fail closed
- trusted entry audit data records the boundary class

## Non-goals

This phase does not introduce:

- new adapter implementation
- framework integration
- distributed governance
- autonomous orchestration
- new risk model
- new runtime execution model


## Runtime Chain Assertions – v0.11.2

`src/runtime_chain_assertions.py` makes guard order executable. The accepted order is Enforcement → Flood Guard → Session Budget → Runtime Guard → Action Ready. Skipped stages, duplicate stages, unknown stages, terminal-stage mismatch and downstream execution after enforcement denial fail closed.
