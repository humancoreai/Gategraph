# GateGraph v0.12.5 Candidate

Release: `v0.12.5_STABLE`
Base: `v0.12.4_STABLE`
Status: `stable`
Phase: Deterministic Registry / Schema Governance

## Scope

v0.12.5 adds deterministic governance around existing registry/schema surfaces. It does not introduce runtime authority, dynamic schema loading, automatic migration, auto-repair, distributed governance, new agent behavior or enforcement changes.

## Added evidence

- `schema_governance_evidence`
- `cross_registry_integrity_evidence`
- `deterministic_export_contract_evidence`
- `schema_drift_visibility_evidence`
- `freeze_snapshot_determinism_evidence`

## Added registry/docs

- `registry/schema_governance_registry.json`
- `docs/SCHEMA_GOVERNANCE.md`

## Release invariant

Declarative structures may be observed, hashed and cross-checked. They must not become execution paths or policy mutation paths.
