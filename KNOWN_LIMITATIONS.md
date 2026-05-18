# Known Limitations – v0.16.8_CANDIDATE

Current release context: v0.16.8_CANDIDATE.

GateGraph intentionally states its limits. This file is part of the security model, not a marketing document.

## Current limitations

- No full runtime sandboxing.
- No kernel isolation.
- No container, VM, Kubernetes, service mesh, or cloud isolation layer.
- No distributed Byzantine-tolerant governance.
- No complete memory governance or context quarantine system.
- No autonomous threat hunting.
- No automatic self-repair.
- No guarantee against unknown future agent strategies.
- No replacement for host OS security, network policy, identity management, or secret manager hardening.
- No guarantee that external transports, providers, or billing systems behave safely.

## Security interpretation

GateGraph reduces specific governance and enforcement failure modes through deterministic gates, explicit budgets, token validation, auditability, and fail-closed behavior. It does not claim to eliminate all agentic AI risk.

## Review rule

Whenever a new surface is added, it must be classified as one of:

- governance logic
- enforcement boundary
- runtime surface
- budget surface
- secret surface
- audit/explain/export surface
- operator surface
- out of scope

Unclassified surfaces should be treated as unsafe until reviewed.
