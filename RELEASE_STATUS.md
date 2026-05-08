# Release Status - GateGraph v0.8.23-evidence-runner-stabilization

Status: Single-node PoC with advisory intelligence, manual review workflow, strictly limited Controlled Apply prototype, and stabilized aggregate evidence runner.

## Changed
- `tests/evidence_ci.py` now executes evidence scripts through `tests/_run_isolated.py`.
- `tests/evidence_supervisor.py` is now a compatibility entrypoint delegating to the same isolated CI runner.
- Controlled Apply evidence is included in the aggregate manifest.

## Unchanged
- Governance, Enforcement, Runtime Guard, Session Budget Guard, HTTP Policy, Secret Provider, External API Adapter, Pattern Engine, Review Workflow, and Controlled Apply behavior are unchanged.
- Enforcement remains the only runtime action gatekeeper.
- Guards remain stop-only.
- Pattern Engine remains proposal-only.
- Review/Controlled Apply still require explicit human gates.
- Audit remains append-only.

## Evidence
- Aggregate runner completed with `Passed: True`.
- Controlled Apply evidence: 7/7 passed.
- Usage simulation: no invariant violations.
- Unusual input simulation: no invariant violations.
- Agent scenario simulation: no invariant violations.
- Core loop and security evidence remain included in the aggregate evidence set.

## Known Limits
- Single-node only.
- Local signing/HMAC model; no production KMS.
- Controlled Apply currently supports rule hardening only.
- No production external API integration.
- Runner is an evidence tool, not a production runtime component.
