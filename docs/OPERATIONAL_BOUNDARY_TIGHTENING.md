# Operational Boundary Tightening – GateGraph v0.11.4_CANDIDATE

Status: stable
Base: v0.11.3_STABLE

## Boundary statement

GateGraph remains a local, deterministic, single-node governance/control plane. This
phase documents and tests unsupported operational shortcuts. It does not add runtime
magic or operational automation.

## Unsupported runtime mutations

- mutating governance decisions outside the existing engines
- altering enforcement outcomes from startup/config layers
- writing audit events through an alternate runtime path
- changing guard order from adapter or packaging code
- modifying release metadata at runtime

## Unsupported startup overrides

- hidden startup modes
- implicit alternate entry points
- public-bind defaults
- automatic server startup during import
- silent fallback from invalid config to default config

## Unsupported operational shortcuts

- treating server mode as production internet exposure
- treating package install as a deployment platform
- skipping Evidence CI during candidate-to-stable promotion
- releasing with generated DB/log/cache/CSV artifacts
- promoting Candidate metadata as Stable metadata

## Unsupported config bypasses

- unknown config sections
- non-positive budget values
- invalid runtime modes
- ENV/config contradictions that imply a new runtime mode
- secret values embedded in example config or task files

## Evidence mapping

- `startup_shutdown_semantics_evidence.py` checks startup/shutdown semantics.
- `runtime_surface_consistency_evidence.py` checks config/runtime mismatch detection.
- `surface_freeze_coupling_evidence.py` checks release/evidence/manifest/doc coupling.
