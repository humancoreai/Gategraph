Release: v0.17.6_CANDIDATE

# GateGraph

Current release: **v0.17.6_CANDIDATE**  
Base: **v0.17.5_STABLE**  
Base stable: **v0.17.5_STABLE**  
Status: **candidate**  
Version: **0.17.6**  
Phase: **Evidence Lifecycle Cleanup Formalization**  
Release focus: **Evidence Lifecycle Cleanup Formalization**
GateGraph is a deterministic governance layer for AI-agent actions. It evaluates requested actions before execution, produces bounded governance decisions, and keeps execution authority outside the model.

## What GateGraph is

GateGraph is designed to sit between an agent or operator workflow and an action surface.

It can:
- evaluate action requests,
- return allow/block/review/approval decisions,
- issue bounded capability-token surfaces,
- produce audit and explainability artifacts,
- run deterministic evidence checks.

## What GateGraph is not

GateGraph is not:
- an autonomous agent,
- a policy-learning system,
- a production internet gateway,
- an identity provider,
- a KMS,
- a multi-node trust fabric,
- a replacement for human approval.

## Current production boundary

Current scope is **local, protected, single-node operation**.

Out of scope for the current release:
- public internet exposure,
- built-in TLS/auth for hostile networks,
- external agent-framework production integration,
- multi-node consensus,
- managed secret infrastructure,
- autonomous policy mutation.

## Quickstart

First verify the local package and supported command surfaces:

```powershell
python tests\fresh_clone_reproducibility_evidence.py
python tests\single_node_cli_evidence.py
```

Minimal local CLI request example:

```powershell
python -m src.cli init --mode single_node --db .\gategraph.db
python -m src.cli evaluate --mode single_node --db .\gategraph.db --task-id CLI-DEMO-READ --actor-id demo-actor --capability read_files --input-source local --data-sensitivity internal
python -m src.cli status --mode single_node --db .\gategraph.db
```

Minimal local HTTP surface example:

```powershell
python -m src.server --help
# Start only in a local/protected environment; public internet exposure is out of scope.
```

Then run the full evidence suite before treating a candidate as release-ready:

```powershell
python tests\evidence_ci.py
```

Expected evidence result:

```text
CI EVIDENCE REPORT
Passed: True
```

## Review surfaces

Core public review files:
- `VERSION.md`
- `RELEASE_STATUS.md`
- `RELEASE_METADATA.json`
- `RELEASE_MANIFEST.json`
- `RELEASE_PROCESS.md`
- `PRODUCTION.md`
- `SECURITY.md`
- `TRUST_MODEL.md`
- `docs/SCOPE_BACKLOG.md`
- `docs/CURRENT_RELEASE.md`
- `docs/RELEASE_v0.17.6_CANDIDATE.md`

## Key documents

| Document | Purpose |
|---|---|
| `TRUST_MODEL.md` | Caller-boundary and trust assumptions. |
| `SECURITY.md` | Security posture and fail-closed expectations. |
| `PRODUCTION.md` | Current production boundary and non-scope. |
| `docs/QUICKSTART.md` | Reproducible local setup and verification path. |
| `docs/CURRENT_RELEASE.md` | Stable alias for the active release surface. |
| `OWASP_AGENTIC_AI_MAPPING.md` | Descriptive mapping to agentic-AI risk categories. |

## Operator playbooks

`playbooks/` contains reference-only operator workflows. Playbooks are documentation and review aids; they do not grant authority, mutate policy, or execute actions.

## Security posture

GateGraph uses fail-closed defaults and separates governance decision surfaces from execution authority. The current release does not add runtime authority, auto-promotion, auto-repair, autonomous policy mutation, or public deployment capability.

## License

Apache-2.0.


## Runtime namespace

Canonical runtime namespace: `gategraph`.

`src/` package is the canonical runtime/governance surface. `gategraph/context/` package is a bounded context-governance extension layer and must not become an alternative governance or execution path.

## Security mapping

`OWASP_AGENTIC_AI_MAPPING.md` is a descriptive mapping from GateGraph evidence surfaces to agentic-AI risk categories. It is a review aid, not a compliance certification or normative policy source.
