# Release Status — GateGraph v0.8.26_STABLE

## Status

Stable recovery point.

`v0.8.26_CROSS_SESSION_BUDGET_CANDIDATE` has been promoted after full Windows Evidence CI reported `Passed: True` on 2026-04-28.

## Stable scope

- Deterministic Governance Layer
- Enforcement as sole Gatekeeper
- Signed Capability Tokens with key rotation evidence
- Runtime Guard and Session Budget Guard
- Runtime Governance escalation states
- Cross-Session Budget Control via single-node Budget Ledger
- HTTP Policy Layer
- Secret references and delayed resolution
- External API Adapter controlled seam
- Audit / Explain reconstruction
- Pattern Engine proposal-only behavior
- Review Workflow and Controlled Apply Human-Gate
- Evidence Runner on Windows

## Validation

Full Evidence CI reported:

```text
Passed: True
Unexpected Allows: 0
Invariant Violations: 0
```

## Production boundary

Still not production-ready for open distributed use. Remaining boundaries:

- Single-node only
- No production KMS
- No distributed budget lock/consensus
- No monitoring/alerting/recovery layer
- No real external provider billing integration

## Stable release document

See `docs/RELEASE_v0.8.26_STABLE.md`.
