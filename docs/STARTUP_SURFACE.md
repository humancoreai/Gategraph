# Startup Surface – GateGraph v0.11.4_STABLE

## Purpose

This document defines the canonical local startup surface for GateGraph after the v0.11.0 packaging baseline.

v0.11.4_STABLE does not introduce new runtime behavior.

## Canonical start paths

```bash
python -m pip install -e .
gategraph --help
python -m src.cli --help
gategraph-server --host 127.0.0.1 --port 8787
python -m src.server --host 127.0.0.1 --port 8787
```

## Required expectations

- CLI and server modules expose `main`.
- `pyproject.toml` scripts point to existing module functions.
- `config.example.yaml` exists as the canonical local config template.
- Runtime `.db`, `.csv`, `.log`, `.tmp`, and `tests/logs/*` artifacts are not release artifacts.
- Missing secrets or invalid runtime configuration fail closed in existing runtime paths.

## Unsupported

- Public internet exposure without reverse-proxy Auth/TLS
- Multi-node startup
- Cloud orchestration
- Docker/Kubernetes/Helm as part of this phase
- UI/dashboard startup
- Alternate governance entry paths

## Health/status surface

The supported status surface remains intentionally minimal: release/version metadata, local/protected server status, existing `/status`, and existing `/monitoring`.

No telemetry stack, dashboard, remote alert router, or cloud monitoring layer is introduced in this phase.


## v0.12.0_STABLE Note

v0.12.0_STABLE preserves this boundary while adding security mapping and token exposure hardening.


Current release surface: `v0.12.1_STABLE`.


Current release surface: v0.12.4_STABLE.

Current release surface: v0.12.7_STABLE


Release surface: v0.12.8_STABLE.

Release surface: v0.14.7_STABLE.


Release surface: v0.15.2_CANDIDATE.
Base stable: v0.14.7_STABLE.
Phase: Recovery Replay Finality Hardening.
