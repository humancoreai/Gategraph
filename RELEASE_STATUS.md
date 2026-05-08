# Release Status - GateGraph v0.8.22-controlled-apply

Status: Single-node PoC with advisory intelligence, manual review workflow, and strictly limited Controlled Apply prototype.

## Added
- `src/controlled_apply.py` for a separate Human-Gate apply path.
- Two distinct reviewer approvals for `approved_for_controlled_apply`.
- Signed Apply Artifacts with TTL, hash validation, and single-use status.
- Initial allowlist: `rule_update` only, and only stricter rule changes.
- Target-state drift detection before execution.
- Controlled Apply audit events.
- `tests/controlled_apply_evidence.py`.
- `docs/CONTROLLED_APPLY.md`.

## Unchanged
- Pattern Engine remains proposal-only.
- Review Workflow still does not apply changes.
- Enforcement remains the only runtime action gatekeeper.
- Guards still stop only; they do not allow.
- Audit remains append-only.
- Secret values remain outside DB persistence.

## Evidence
- Controlled Apply evidence cases were run individually due local runner/process instability.
- Confirmed: manual review required, two distinct Human-Gates required, same-reviewer double approval blocked, unsupported/looser changes blocked, strict rule hardening executes and audits, replay blocked.
- Target-drift test exists; local aggregate execution was environment-sensitive during packaging.

## Known Limits
- Single-node only.
- Local HMAC apply-key model; no production KMS.
- Controlled Apply currently supports rule hardening only.
- No API production integration.
- No distributed review identity model.
