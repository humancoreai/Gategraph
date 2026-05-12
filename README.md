# GateGraph

Current release: **v0.15.2_CANDIDATE**  
Base: **v0.15.1_STABLE**  
Base stable: **v0.15.1_STABLE**  
Status: **candidate**  
Version: **0.15.2**  
Phase: **Promotion semantics cleanup and stable-surface separation**  
Release focus: **Promotion Semantics Cleanup / Stable-Surface Separation / Release-Hygiene Hardening**

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

```powershell
python tests\evidence_ci.py
```

Expected result:

```text
CI EVIDENCE REPORT
Passed: True
```

For a first practical local check, use:

```powershell
python tests\fresh_clone_reproducibility_evidence.py
python tests\promotion_surface_matrix_evidence.py
python tests\release_process_guard_evidence.py
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
- `docs/RELEASE_v0.15.2_CANDIDATE.md`

## Security posture

GateGraph uses fail-closed defaults and separates governance decision surfaces from execution authority. The current release does not add runtime authority, auto-promotion, auto-repair, autonomous policy mutation, or public deployment capability.

## License

Apache-2.0.


## Runtime namespace

Canonical runtime namespace: `gategraph`.

Legacy or compatibility surfaces must not be presented as the canonical runtime namespace.

`src/` package is the canonical runtime/governance surface

OWASP_AGENTIC_AI_MAPPING.md

`gategraph/context/` package is a bounded context-governance extension layer

The bounded context-governance extension layer must not become an alternative governance or execution path.
