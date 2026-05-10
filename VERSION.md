# GateGraph Version

Current: v0.8.17-block-e-documentation-reality-check

## v0.8.17-block-e-documentation-reality-check
- Aligns README, SECURITY.md, docs/SECURITY.md, VERSION.md, and RELEASE_STATUS.md with the actual v0.8.16 system state.
- Adds explicit current-limitations / not-production-ready framing.
- Removes obsolete documentation claims that token signing, runtime/cost controls, or API integration are entirely absent.
- Adds `docs/BLOCK_E_DOCUMENTATION_REALITY.md`.
- Production governance/enforcement/runtime semantics unchanged.

## v0.8.16-block-d-audit-explain-evidence
- Adds read-only audit/explain trace reconstruction via `src/explain_trace.py`.
- Adds Block D evidence for completed, Enforcement-blocked, HTTP Policy-blocked, and secret-backed flows.
- Confirms that raw secret values do not appear in reviewer-facing trace output.
- Production governance/enforcement/runtime semantics unchanged.

## v0.8.15-block-c-stress-evidence
- Adds Block C stress evidence for runaway/cost behavior under API-shaped flows.
- Proves session-level micro-flood blocking, agent-level fan-out blocking, exact budget-boundary behavior, and same-task repeated-action runtime stops.
- Adds `tests/block_c_stress_evidence.py` and `docs/BLOCK_C_STRESS_EVIDENCE.md`.
- Production governance/enforcement/runtime semantics unchanged.

## v0.8.14 runner-harness-hardening
- Evidence runner hardened with file-backed subprocess execution and timeout classification.
- Production governance/enforcement/runtime semantics unchanged.

## v0.8.14-security-finesse
- Adds Block B security-finesse evidence for secret leak checks, HTTP policy edge cases, and combined token failure behavior.
- Hardens HTTP path-prefix matching with boundary-aware semantics.
