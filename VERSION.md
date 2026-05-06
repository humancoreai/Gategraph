# GateGraph Version

Current: v0.8.15-block-c-stress-evidence

## v0.8.15-block-c-stress-evidence
- Adds Block C stress evidence for runaway/cost behavior under API-shaped flows.
- Proves session-level micro-flood blocking, agent-level fan-out blocking, exact budget-boundary behavior, and same-task repeated-action runtime stops.
- Adds `tests/block_c_stress_evidence.py` and `docs/BLOCK_C_STRESS_EVIDENCE.md`.
- Production governance/enforcement/runtime semantics unchanged.

Previous: v0.8.14-runner-harness-hardening / v0.8.14-security-finesse

## v0.8.14 runner-harness-hardening
- Evidence runner hardened with file-backed subprocess execution and timeout classification.
- Production governance/enforcement/runtime semantics unchanged.

## v0.8.14-security-finesse
- Adds Block B security-finesse evidence for secret leak checks, HTTP policy edge cases, and combined token failure behavior.
- Hardens HTTP path-prefix matching with boundary-aware semantics.
