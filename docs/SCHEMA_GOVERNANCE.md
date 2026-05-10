# Schema Governance — v0.12.5 Candidate

GateGraph v0.12.5 introduces a deterministic schema/registry governance surface for already-existing declarative structures.

## Invariants

- Schema governance is descriptive only.
- It does not migrate, repair, load or execute schemas dynamically.
- Registry references must resolve to concrete repository files.
- Export/import contracts are deterministic artifacts, not runtime authority.
- Schema drift is visible as evidence, not corrected automatically.
- Freeze snapshots remain reconstructable and non-authoritative.

## Non-scope

- No distributed governance.
- No dynamic plugin loading.
- No automatic schema migration.
- No auto-repair.
- No new runtime capability.
- No policy mutation.

## Evidence

- `schema_governance_evidence.py`
- `cross_registry_integrity_evidence.py`
- `deterministic_export_contract_evidence.py`
- `schema_drift_visibility_evidence.py`
- `freeze_snapshot_determinism_evidence.py`
