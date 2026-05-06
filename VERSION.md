# GateGraph Version

Current: v0.8.23-evidence-runner-stabilization


## v0.8.23-evidence-runner-stabilization
- Stabilizes aggregate evidence execution without changing Governance, Enforcement, Runtime, HTTP, Secret, Pattern, Review, or Controlled Apply semantics.
- Routes aggregate runs through `tests/_run_isolated.py`, which calls evidence entrypoints normally and hard-exits after completion to avoid interpreter shutdown hangs.
- Adds Controlled Apply evidence to the aggregate manifest.
- Replaces the legacy multiprocessing supervisor with a compatibility wrapper around the isolated, file-backed CI runner.
- Evidence aggregation now completes with `Passed: True` on the current test set.

## v0.8.22-controlled-apply
- Adds strictly limited Controlled Apply path behind separate two-person Human-Gate.
- Adds signed, TTL-bound, single-use Apply Artifacts.
- Initial scope supports only validated rule hardening (`rule_update`); unsupported or loosening changes fail closed.
- Adds target-state drift detection before execution.
- Adds append-only audit events for controlled apply request/approval/execution.
- Adds `src/controlled_apply.py`, `tests/controlled_apply_evidence.py`, and `docs/CONTROLLED_APPLY.md`.
- Existing Governance/Enforcement/Runtime/Pattern/Review invariants remain unchanged.

## v0.8.19-pattern-priority-scoring
- Adds advisory Pattern Engine priority and score metadata (`P0`–`P3`, numeric score, score basis).
- Persists `priority`, `score`, and `score_basis` on proposals.
- Keeps Pattern Engine strictly proposal-only; no runtime rule/policy/budget/secret/token mutation.
- Adds `tests/pattern_priority_scoring_evidence.py` and `docs/PATTERN_ENGINE_PRIORITY_SCORING.md`.
- Production governance/enforcement/runtime semantics unchanged.

## v0.8.18-pattern-engine-intelligence
- Adds `analyze_audit_patterns()` for multi-stage audit pattern analysis.
- Pattern Engine can propose review items for repeated HTTP Policy, Secret Provider, Enforcement, and guard-stage blocks.
- Adds `tests/pattern_intelligence_evidence.py` and `docs/PATTERN_ENGINE_INTELLIGENCE.md`.
- Production governance/enforcement/runtime semantics unchanged.

## v0.8.17-block-e-documentation-reality
- Aligns README, SECURITY.md, docs/SECURITY.md, VERSION.md, and RELEASE_STATUS.md with the actual system state.
- Adds explicit current-limitations / not-production-ready framing.
- Removes obsolete documentation claims that token signing, runtime/cost controls, or API integration are absent.
- Adds `docs/BLOCK_E_DOCUMENTATION_REALITY.md`.
- Production governance/enforcement/runtime semantics unchanged.

## v0.8.16-block-d-audit-explain-evidence
- Adds read-only audit/explain trace reconstruction via `src/explain_trace.py`.
- Adds Block D evidence for completed, Enforcement-blocked, HTTP Policy-blocked, and secret-backed flows.
- Confirms raw secret values do not appear in reviewer-facing trace output.
- Production governance/enforcement/runtime semantics unchanged.

## v0.8.15-block-c-stress-evidence
- Adds Block C stress evidence for runaway/cost behavior under API-shaped flows.
- Proves session-level micro-flood blocking, agent-level fan-out blocking, exact budget-boundary behavior, and same-task repeated-action runtime stops.
- Adds `tests/block_c_stress_evidence.py` and `docs/BLOCK_C_STRESS_EVIDENCE.md`.
- Production governance/enforcement/runtime semantics unchanged.

## v0.8.14-runner-harness-hardening
- Evidence runner hardened with file-backed subprocess execution and timeout classification.
- Production governance/enforcement/runtime semantics unchanged.

## v0.8.13-security-finesse
- Adds Block B security-finesse evidence for secret leak checks, HTTP policy edge cases, and combined token failure behavior.
- Hardens HTTP path-prefix matching with boundary-aware semantics.
