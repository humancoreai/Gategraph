# Release Status – v0.11.5_STABLE

Status: stable

Base: v0.11.4_STABLE

Phase: Security Mapping + Token Exposure Hardening

Promotion basis:
- promoted from v0.11.5_CANDIDATE after full Windows Evidence CI reported Passed: True on 2026-05-08
- no governance logic change during stable promotion
- no runtime logic change during stable promotion
- no enforcement logic change during stable promotion

Scope:
- add explicit security model and known limitation documentation
- map common agentic AI risk classes to existing GateGraph controls and evidence
- centralize token / Authorization / sensitive-field redaction helpers
- prove audit, explain, and monitoring surfaces do not expose raw token, bearer, base64 token, or secret material
- preserve the existing single-node/local protected runtime surface

Out of scope:
- no executable runtime mode implementation
- no governance changes
- no enforcement changes
- no adapter changes
- no new token authority
- no budget expansion
- no secret/tool access expansion
- no agentic behavior
- no multi-node/distributed governance
- no cloud orchestration
- no Docker/Kubernetes/Helm/service mesh
- no UI/dashboard
