# Controlled Apply v0.8.22

## Scope

Controlled Apply is an optional, narrow path for deterministic, human-gated application of already reviewed proposals.

Initial implementation deliberately supports only:

- `rule_update`
- existing active rules only
- stricter `risk_threshold`, `severity`, or `decision`
- increased `priority`
- non-empty rationale update

Not supported:

- Enforcement changes
- token/keyring changes
- secret access or rotation
- policy deletion
- budget loosening
- code/runtime mutation
- external API integration

## Flow

1. Proposal is created by Pattern Engine.
2. Review Workflow marks it `approved_for_manual_action`.
3. Controlled Apply requires two distinct reviewers with `approved_for_controlled_apply`.
4. System creates a signed TTL-bound Apply Artifact.
5. Executor validates signature, hash, TTL, status, scope, and target-state drift.
6. Only then is the allowlisted mutation applied.
7. Audit event records request/approval/execution.

## Invariants

- Pattern Engine still does not decide.
- Review Workflow still does not apply.
- Controlled Apply does not bypass Governance/Enforcement for runtime actions.
- Apply Artifacts are single-use.
- Target drift fails closed.
- Unsupported or loosening changes fail closed.

## Evidence

Evidence script: `tests/controlled_apply_evidence.py`

Covered cases:

- no Controlled Apply before manual review
- two distinct Human-Gates required
- same-reviewer double approval blocked
- unsupported/looser changes blocked
- strict rule hardening executes and audits
- replay blocked
- target drift blocked
