# GateGraph

Current release: **v0.16.8_STABLE**  
Base: **v0.16.7_STABLE**  
Base stable: **v0.16.7_STABLE**  
Status: **stable**  
Version: **0.16.8**  
Phase: **Release Status Assertion Policy**  
Release focus: **Release Status Assertion Policy**

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
- `docs/RELEASE_v0.16.8_STABLE.md`

## Security posture

GateGraph uses fail-closed defaults and separates governance decision surfaces from execution authority. The current release does not add runtime authority, auto-promotion, auto-repair, autonomous policy mutation, or public deployment capability.

## License

Apache-2.0.


## Runtime namespace

Canonical runtime namespace: `gategraph`.

`src/` package is the canonical runtime/governance surface. `gategraph/context/` package is a bounded context-governance extension layer and must not become an alternative governance or execution path.

## Security mapping

`OWASP_AGENTIC_AI_MAPPING.md` is a descriptive mapping from GateGraph evidence surfaces to agentic-AI risk categories. It is a review aid, not a compliance certification or normative policy source.
