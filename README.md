# GateGraph

**Deterministic governance layer for AI-assisted task execution.**

GateGraph sits before execution. It decides whether a requested action may proceed, under what conditions, and produces a signed, bounded capability token as the sole execution authority. It does not execute actions. It does not create goals. It does not change policy autonomously.

Current release: **v0.12.0_CANDIDATE**  
Base stable: **v0.11.9_STABLE**  
License: Apache 2.0

---

## What it does

An agent or service submits a task evaluation request. GateGraph evaluates it deterministically through a fixed chain:

```
Task Request
→ Caller Boundary Validation   (required fields enforced at adapter)
→ Risk Engine                  (deterministic risk scoring)
→ Rule Engine                  (policy match, conflict resolution)
→ Governance Decision          (allow / warn / require_review / block)
→ Capability Token             (HMAC-signed, task-bound, TTL-limited)
→ Enforcement Gate             (token verification before any execution)
→ Flood Guard                  (rate / cost window limits)
→ Session Budget Guard         (per-session cost and task caps)
→ Runtime Guard                (step / time / cost limits during execution)
→ Audit Log                    (append-only, replay-consistent)
```

Every stage is ordered. Skipping stages fails closed. The chain order is an executable invariant — `runtime_chain_assertions.py` verifies it, not just documents it.

---

## Core principles

| Principle | Meaning |
|---|---|
| **Fail-closed** | Unknown, missing, or ambiguous inputs deny by default |
| **Deterministic** | Same input + same policy = same decision, always |
| **No autonomy** | GateGraph enforces rules; it does not write them |
| **Append-only audit** | Decision history is never modified after the fact |
| **Enforcement is mandatory** | No execution without a valid capability token |
| **Human authority is final** | `require_review` and `require_approval` block without a human gate |

---

## Architecture

```
CLI / HTTP Server
      ↓
  service_adapter          ← caller boundary validation (required fields enforced here)
      ↓
  governance.evaluate_task ← single entry point; TrustedEntryContext required
      ↓
  Risk Engine + Rule Engine + Event Logger + Budget Ledger + Token
      ↓
  Enforcement Gate
      ↓
  Runtime Chain (Flood / Session Budget / Runtime Guard)
      ↓
  Action-ready or Stop
      ↓
  Audit / Operator Layer
```

**CLI and HTTP server both use the same `service_adapter` path.** There is no separate code path for server-mode evaluation. Governance logic is never duplicated or bypassed.

**Canonical runtime namespace:** the executable CLI/server entry points use `src.cli:main` and `src.server:main` as defined in `pyproject.toml`. The `src/` package is the canonical runtime/governance surface. The `gategraph/context/` package is a bounded context-governance extension layer used for context classification, provenance, and instruction/data separation; it must not become an alternative governance or execution path.

**Security mapping:** the OWASP Agentic AI mapping is documented in `OWASP_AGENTIC_AI_MAPPING.md` and is part of the release surface, not an autonomous risk-scoring system.

---

## Quick start

### Requirements

- Python 3.11+
- No external dependencies beyond the standard library

### Setup

```bash
git clone https://github.com/humancoreai/Gategraph.git
cd Gategraph
cp config.example.yaml config.yaml
python -m pip install -e .
```

### CLI evaluation

```bash
python -m src.cli evaluate \
  --task-id "task-001" \
  --task-type "agent_file_operations" \
  --capabilities "read_files" \
  --input-source "local" \
  --data-sensitivity "internal"
```

### HTTP server (local/protected only)

```bash
python -m src.server --host 127.0.0.1 --port 8787
```

```bash
curl -s -X POST http://127.0.0.1:8787/evaluate \
  -H "content-type: application/json" \
  -d '{
    "task_id": "task-001",
    "task_type": "agent_file_operations",
    "requested_capabilities": ["read_files"],
    "input_source": "local",
    "data_sensitivity": "internal"
  }'
```

Available endpoints: `POST /evaluate`, `GET /status`, `GET /monitoring`

---

## Configuration

`config.example.yaml` documents all available settings:

```yaml
mode: single_node
db_path: gategraph.db
actor_id: local-actor
system_budget_units: 100
session_budget:
  max_session_cost_units: 50
  max_session_tasks: 20
flood_guard:
  window_seconds: 60
  max_tasks_per_window: 20
runtime_budget:
  max_steps: 20
  max_runtime_seconds: 300
```

---

## Running evidence

```bash
# Full evidence suite
python tests/evidence_ci.py

# Individual evidence modules
python tests/caller_boundary_evidence.py
python tests/runtime_chain_order_evidence.py
python tests/release_process_guard_evidence.py
python tests/governance_freeze_evidence.py
```

---

## Caller boundary

The public evaluation entry point requires three explicit fields. Omitting or using invalid values fails closed:

| Field | Required values |
|---|---|
| `input_source` | `"local"`, `"trusted"`, `"untrusted"`, `"external"` |
| `data_sensitivity` | `"public"`, `"internal"`, `"confidential"`, `"secret"` |
| `secrets_involved` | `true` / `false` |

Direct calls to `governance.evaluate_task()` without a `TrustedEntryContext` are denied by default since v0.10.0.

---

## Production scope

GateGraph is **production-ready for single-node, local/protected deployment**.

**In scope:**
- CLI evaluation
- Local HTTP adapter (`127.0.0.1` default bind)
- Deterministic governance and enforcement
- Runtime, session, flood, and budget guards
- Read-only monitoring export
- Append-only audit with replay consistency

**Explicitly out of scope (current version):**
- Public internet exposure
- Authentication / TLS (reverse proxy required for any external access)
- Multi-node or distributed governance
- KMS-backed secret management
- Asymmetric capability token signing
- External agent framework integration
- UI / dashboard
- Automated alert routing

---

## Security model

- HTTP server binds to `127.0.0.1` by default; `0.0.0.0` emits an explicit warning
- Request body bounded at 64 KiB
- Stack traces are never returned to clients
- Capability tokens are HMAC-signed and task-bound with TTL
- Token signing key is env-backed (not hardcoded); missing key fails closed
- Audit log is append-only; no DELETE or UPDATE on event history
- See `SECURITY.md` and `docs/THREAT_MODEL.md` for full threat model

---

## Key documents

| Document | Purpose |
|---|---|
| `INVARIANTS.md` | Decision, authority, audit, and release invariants |
| `TRUST_MODEL.md` | What GateGraph trusts and what it does not |
| `docs/THREAT_MODEL.md` | Threat classes and expected controls |
| `docs/KNOWN_GAPS_ROADMAP.md` | Open gaps and planned phases |
| `PRODUCTION.md` | Explicit production scope and responsibility model |
| `docs/DEPLOYMENT_BOUNDARY.md` | Supported/unsupported/unsafe deployment boundary |
| `docs/INVARIANT_REGISTRY.md` | Stable invariant IDs (INV-001–INV-015) with evidence mapping |
| `GOVERNANCE.md` | Rule structure and decision logic |
| `docs/ARCHITECTURE.md` | Layer separation and data flow |
| `docs/SERVER_MODE.md` | HTTP adapter invariants and endpoints |
| `RELEASE_PROCESS.md` | How releases are built, verified, and promoted |

---

## Release integrity

Releases are built deterministically via `tools/build_release.py`. Every release includes:

- `RELEASE_MANIFEST.json` with SHA256 per file
- `tools/verify_release.py` for independent verification
- `tools/release_process_guard.py` to prevent pre-release/stable metadata drift
- `.db` files excluded from release artifacts by default

```bash
python tools/verify_release.py dist/GateGraph_v0.12.0_CANDIDATE.zip
```

---

## What GateGraph is not

- Not an agent framework
- Not a policy authoring system
- Not a distributed consensus system
- Not an internet-facing API without additional hardening
- Not a replacement for human judgment on `require_review` decisions

---

## Contributing

See `CONTRIBUTING.md` and `RELEASE_PROCESS.md`.  
Security issues: see `SECURITY.md`.

---

## License

Apache 2.0 — see `LICENSE`.


See also `docs/STARTUP_SURFACE.md` for canonical local start paths and operational start-surface expectations.
