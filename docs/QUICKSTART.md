# GateGraph Quickstart

Release: v0.15.7_STABLE  
Base: v0.14.7_STABLE  
Status: stable

## Local verification

```powershell
python -m pip install -e .
python tests\evidence_ci.py
```

## Single-node CLI smoke check

```powershell
gategraph --help
gategraph-server --help
```

## Boundary

This release is intended for local single-node verification and repository review. It is not a distributed production deployment and does not grant autonomous enforcement outside the explicit GateGraph evidence surfaces.

## Hygiene expectations

Do not commit runtime databases, generated evidence outputs, local ZIPs, CSV simulation artifacts, secrets or machine-specific IDE directories.
