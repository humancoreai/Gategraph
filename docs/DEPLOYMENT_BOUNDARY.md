# Deployment Boundary – GateGraph v0.11.4_STABLE

## Purpose

This document defines the supported deployment surface for the Phase B packaging baseline.

v0.11.4_STABLE does not introduce new runtime behavior. It makes the existing single-node system installable and easier to start reproducibly.

## Supported

- Python 3.11+
- Local editable install: `pip install -e .`
- Single-node CLI execution
- Local/protected HTTP server
- Default bind to `127.0.0.1`
- SQLite-backed local state
- Reverse-proxy deployment only when external exposure is required
- External TLS/Auth handled outside GateGraph

## Unsupported

- Direct public internet exposure
- Built-in TLS termination
- Built-in authentication/authorization layer
- Multi-node governance
- Distributed budget ledgers
- Distributed audit consensus
- Kubernetes/Helm/service-mesh deployment
- Cloud-managed runtime orchestration
- UI/dashboard deployment

## Unsafe without additional controls

- Binding the HTTP server to `0.0.0.0`
- Reusing local test secrets in a shared environment
- Writing runtime `.db` files into a source-controlled repository
- Treating monitoring exports as an authorization channel
- Running GateGraph as a public API without reverse-proxy Auth/TLS

## Required local start paths

### Editable install

```bash
python -m pip install -e .
```

### CLI

```bash
gategraph evaluate --task-id task-001 --task-type agent_file_operations --capabilities read_files --input-source local --data-sensitivity internal
```

Equivalent module path remains supported:

```bash
python -m src.cli evaluate --task-id task-001 --task-type agent_file_operations --capabilities read_files --input-source local --data-sensitivity internal
```

### HTTP server

```bash
gategraph-server --host 127.0.0.1 --port 8787
```

Equivalent module path remains supported:

```bash
python -m src.server --host 127.0.0.1 --port 8787
```

## Environment expectations

- Token signing key must not be hardcoded.
- Missing required secrets fail closed.
- Configuration should be copied from `config.example.yaml` to `config.yaml` for local use.
- Runtime artifacts must not be committed.

## Invariant

Packaging must not create an alternative governance path. All evaluation still flows through the existing service adapter and TrustedEntryContext enforcement.


See also `docs/STARTUP_SURFACE.md` for canonical local start paths and operational start-surface expectations.


## v0.12.0_STABLE Note

v0.12.0_STABLE preserves this boundary while adding security mapping and token exposure hardening.


Current release surface: `v0.12.1_STABLE`.


Current release surface: v0.12.4_STABLE.

Current release surface: v0.12.7_STABLE


Release surface: v0.12.8_STABLE.

Release surface: v0.13.5_STABLE.


Release surface: v0.13.6_CANDIDATE.
Base stable: v0.13.5_STABLE.
Phase: Recovery Replay Finality Hardening.
