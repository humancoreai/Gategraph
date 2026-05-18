# GateGraph v0.17.7_STABLE

Base: v0.17.7_STABLE  
Status: stable  
Phase: Release SSOT Consolidation

This candidate focuses on reducing recurring Candidate/Stable release-token drift. It adds a descriptive release-status token registry and evidence gate so status, current release, base, and future candidate semantics are checked from one explicit surface.

No runtime, enforcement, governance, adapter, server, or policy logic is changed. No evidence tests are removed.

## Scope

- Centralize release/status/future-candidate token expectations.
- Keep checks descriptive and fail-closed.
- Preserve manual Candidate → Stable promotion gates.
- Reduce future hardcoded Candidate/Stable assertion drift.

## Non-scope

- Multi-node implementation.
- Automatic promotion.
- Automatic repair.
- Evidence pruning.
- Runtime behavior changes.
