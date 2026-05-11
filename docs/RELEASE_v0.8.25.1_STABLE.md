# GateGraph v0.8.25.1_STABLE

Status: STABLE  
Basis: `v0.8.25.1_RUNNER_HARDENING_STABLE`  
Validation: full Windows evidence run reported `Passed: True` on 2026-04-28.

## Stable scope

This release consolidates two hardening blocks:

1. Runtime Governance / Runaway Cost Control
   - deterministic escalation states: `normal`, `degraded`, `throttled`, `blocked`
   - stricter `max_cost_for_action` constraints in Runtime Guard
   - non-positive cost values fail closed
   - loop signals can only tighten constraints

2. Evidence Runner Hardening
   - deterministic pass/fail/timeout selftest path
   - Windows process-tree termination via `taskkill /T /F` plus direct kill fallback
   - POSIX watchdog path for bounded subprocess execution
   - brittle nested child-hang case removed from the release gate

## Evidence summary

The Windows CI evidence run completed with:

- `Passed: True`
- Runner selftest: 3/3 passed
- Runtime stress evidence: 14/14 passed
- Session budget evidence: 6/6 passed
- Guard orchestration evidence: 5/5 passed
- Reason normalization evidence: 6/6 passed
- Scale safety evidence: 4/4 passed
- External API evidence: 7/7 passed
- Runaway cost evidence: 5/5 passed
- Capability token hardening evidence: 5/5 passed
- Key rotation evidence: 4/4 passed
- Secret/API integration evidence: 4/4 passed
- HTTP policy evidence: 4/4 passed
- Security finesse evidence: 7/7 passed
- Block C stress evidence: 4/4 passed
- Block D audit/explain evidence: 4/4 passed
- Core loop: 20/20 isolated, 20/20 accumulated
- Runtime guard: 6/6 passed
- Pattern engine: 3/3 passed
- Pattern intelligence: 4/4 passed
- Controlled apply: 7/7 passed

No unexpected allows and no invariant violations were reported.

## Preserved invariants

- No action without a valid capability token.
- Enforcement remains the only action gatekeeper.
- Guards only stop; they do not grant authority.
- Pattern Engine remains advisory and proposal-only.
- Review Workflow does not apply changes automatically.
- Controlled Apply requires the Human-Gate path.
- Audit remains append-only.
- Secret values are not written into audit/evidence.
- HTTP access remains allowlist-based and HTTPS-only.
- Uncertainty fails closed.

## Known limits

- Single-node proof-of-concept.
- No production KMS / OS keychain lifecycle.
- No distributed budget coordination.
- No real provider billing integration.
- No monitoring/alerting subsystem.
- External API integration is still a controlled seam, not unrestricted production connectivity.

## Release note

This version is considered stable for the current local evidence scope. It should be used as the next recovery point before adding new integration features.
