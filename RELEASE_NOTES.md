# GateGraph v0.9.1_CANDIDATE Release Notes

Base: v0.9.0_STABLE

## Purpose

v0.9.1 closes boundary and release-integrity gaps identified after the v0.9.0 external review baseline.

## Added

- Explicit `TRUST_MODEL.md`.
- Caller boundary evidence.
- Release integrity evidence.
- Minimal external review documents: `CONTRIBUTING.md`, `CHANGELOG.md`, `RELEASE_PROCESS.md`, `LICENSE`.

## Changed

- Adapter requests now require explicit `input_source`, `data_sensitivity`, and `secrets_involved` fields.
- Release builder and verifier now reject empty manifests, undeclared files, forbidden local artifacts, and non-deterministic ZIP metadata.

## Not Changed

- No new governance decision logic.
- No new runtime model.
- No new risk model.
- No automatic reclassification.
- No semantic inspection.
- No multi-node behavior.
