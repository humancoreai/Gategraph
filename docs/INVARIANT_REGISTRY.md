# GateGraph Invariant Registry

This registry gives stable IDs to the core governance invariants used by the v0.9.3 governance freeze snapshot.

| ID | Invariant | Layer | Criticality | Primary evidence |
|---|---|---|---|---|
| INV-001 | Governance decisions are centralized | Governance | critical | `guard_orchestration_evidence` |
| INV-002 | Enforcement is mandatory | Enforcement | critical | `capability_token_hardening_evidence` |
| INV-003 | Runtime never overrides governance | Runtime | critical | `runtime_stress_evidence` |
| INV-004 | Audit paths are append-only | Audit | critical | `governance_archive_replay_evidence` |
| INV-005 | Replay remains deterministic | Replay | critical | `archive_integrity_replay_consistency_evidence` |
| INV-006 | Capability tokens are mandatory for protected execution | Enforcement | critical | `key_rotation_evidence` |
| INV-007 | Pattern engine remains proposal-only | Governance | critical | `pattern_engine_tests` |
| INV-008 | Fail-closed applies under uncertainty | System | critical | `operational_hardening_evidence` |
| INV-009 | Adapters have no governance authority | Integration | critical | `caller_boundary_evidence` |
| INV-010 | Delegation requires explicit authorization | Multi-agent | critical | `multi_agent_architecture_evidence` |
| INV-011 | Budget limits cannot escalate implicitly | Runtime | high | `cross_session_budget_evidence` |
| INV-012 | Explainability remains structured and deterministic | Explain | high | `reason_normalization_evidence` |
| INV-013 | Hidden runtime paths are forbidden | Runtime | critical | `runtime_cost_governance_evidence` |
| INV-014 | Adapter paths must not alter replay semantics | Integration | high | `governance_archive_replay_evidence` |
| INV-015 | Human review gates remain binding | Human review | high | `human_review_queue_evidence` |

| INV-016 | Recovery never creates authority | Recovery | critical | `recovery_idempotency_evidence` |

| INV-017 | Replay objects remain non-executable references | Replay | critical | `replay_reference_integrity_evidence` |

| INV-018 | Release/version/surface claims remain synchronized | Release | critical | `release_surface_sync_evidence` |

## Minimal requirement

Each critical invariant must remain referencable and must be covered by at least one evidence group or explicit boundary document.

This registry is not a compliance framework. It is a compact traceability baseline.

Current release surface: v0.12.4_STABLE
