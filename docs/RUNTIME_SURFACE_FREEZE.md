# Runtime Surface Freeze – GateGraph v0.11.4_STABLE

Status: stable
Base: v0.11.3_STABLE
Phase: Operational Consistency / Runtime Surface Tightening

## Purpose

This document makes the supported runtime surface explicit. It does not introduce a
new runtime capability, governance decision path, enforcement rule, adapter, agentic
behavior, network mode, deployment platform, or UI.

## Supported runtime surface

Canonical local surfaces:

- `gategraph init`
- `gategraph evaluate --task <task.json>`
- `gategraph status`
- `gategraph export-monitoring --out <file.json>`
- `gategraph-server --host 127.0.0.1 --port <port>` for local/protected adapter use only

Canonical metadata surfaces:

- `RELEASE_METADATA.json`
- `RELEASE_MANIFEST.json`
- `pyproject.toml`
- `docs/STARTUP_SURFACE.md`
- `docs/RUNTIME_SURFACE_FREEZE.md`
- `docs/OPERATIONAL_BOUNDARY_TIGHTENING.md`
- Evidence entries in `tests/evidence_ci.py`

## Exit-code semantics

- CLI help exits with `0`.
- CLI argument or startup misuse exits non-zero.
- CLI controlled runtime/config failure exits `2` through the adapter error boundary.
- CLI evaluation denial exits `1` without exposing an execution token.
- Successful CLI operations exit `0`.
- Server `KeyboardInterrupt` shutdown exits `0` and calls `server_close()`.

## Unsupported runtime surface

The following are unsupported and must not be described as release capabilities:

- alternative runtime modes beyond the existing local/single-node surfaces
- public internet server deployment
- Docker, Kubernetes, Helm, service mesh or cloud orchestration
- UI/dashboard operation
- multi-node orchestration
- adapter-side governance decisions
- runtime self-repair or fallback execution
- bypassing the guard chain through direct internal module calls

## Freeze coupling

The release is acceptable only when these surfaces agree:

| Surface | Source of truth |
|---|---|
| Manifest | `RELEASE_MANIFEST.json` |
| Release claims | `RELEASE_METADATA.json` |
| Startup contract | `docs/STARTUP_SURFACE.md` |
| Runtime contract | `docs/RUNTIME_SURFACE_FREEZE.md` |
| Operational non-scope | `docs/OPERATIONAL_BOUNDARY_TIGHTENING.md` |
| Evidence scope | `tests/evidence_ci.py` |

Any mismatch is release drift and must fail evidence.
