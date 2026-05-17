# OWASP Agentic AI Risk Mapping – v0.16.7_STABLE

This mapping was formally bumped during v0.16.7_STABLE release hygiene. It remains an internal review aid, not a certification claim, and does not assert complete coverage of any external standard.

| Risk | Status | Existing Coverage | Evidence | Remaining Gap |
|---|---|---|---|---|
| Prompt Injection | partial | Untrusted content is treated as data in core and agent scenarios; rule decisions can require review or block unsafe actions. | `tests/agent_scenarios.py`, `tests/unusual_inputs.py`, `tests/security_finesse_evidence.py` | No full memory/context quarantine system yet. |
| Tool Abuse | partial | Actions require capability tokens and enforcement; unknown or wrong capabilities fail closed. | `tests/test_loop.py`, `tests/capability_token_hardening_evidence.py` | Tool sandboxing is not complete runtime containment. |
| Agent Loops | covered | Runtime guard limits steps, repeated action signatures, runtime, and cost. | `tests/runtime_guard_tests.py`, `tests/runtime_stress_evidence.py`, `tests/runaway_cost_evidence.py` | Does not claim protection against every distributed loop topology. |
| Cost Runaway | covered | Session, actor, runtime, flood, and cross-session budget controls. | `tests/session_budget_evidence.py`, `tests/cross_session_budget_evidence.py`, `tests/runtime_cost_governance_evidence.py`, `tests/block_c_stress_evidence.py` | External provider billing systems remain outside GateGraph. |
| Capability Replay | covered | Tokens are signed, task-bound, expiring, revocable, and claim-checked. | `tests/capability_token_hardening_evidence.py`, `tests/key_rotation_evidence.py` | Does not replace secure transport/session handling by the host system. |
| Secret Leakage | partial | Secret values resolve only after full guard pass and are excluded from audit/explain outputs. | `tests/secret_api_integration_evidence.py`, `tests/security_finesse_evidence.py`, `tests/token_exposure_evidence.py` | Host environment secret storage is outside GateGraph. |
| Cross-Agent Escalation | partial | Actor/session budgets, flood guard, and multi-agent architecture boundaries exist. | `tests/multi_agent_architecture_evidence.py`, `tests/cross_session_budget_evidence.py` | Delegation-chain semantics and transitive authority hardening remain future work. |
| Context Poisoning | open | Some untrusted input treatment exists. | `tests/agent_scenarios.py` | No complete provenance, quarantine, or memory governance layer yet. |
| Runtime Escalation | partial | Runtime surface, API boundary, startup/shutdown, and freeze coupling evidence constrain known surfaces. | `tests/runtime_boundary_hardening_evidence.py`, `tests/api_boundary_split_evidence.py`, `tests/runtime_surface_consistency_evidence.py` | No kernel/process/container isolation guarantee. |
| Human Override Abuse | partial | Controlled apply and review workflows constrain rule hardening and review lifecycle. | `tests/controlled_apply_evidence.py`, `tests/review_workflow_evidence.py`, `tests/human_review_queue_evidence.py` | Emergency override and organization-level access control remain host/process concerns. |
| Sensitive Observability Leakage | partial | v0.11.9 centralizes token/auth redaction and tests audit/explain/monitoring boundaries. | `tests/capability_token_redaction_evidence.py`, `tests/token_exposure_evidence.py` | Requires ongoing review whenever new export surfaces are added. |

## Status definitions

- `covered`: deterministic evidence exists for the scoped GateGraph claim.
- `partial`: meaningful controls exist, but the risk class is broader than GateGraph's current scope.
- `open`: not implemented as a dedicated GateGraph control.
- `intentionally_out_of_scope`: outside current project responsibility.
