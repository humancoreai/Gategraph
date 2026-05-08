# Release Status — GateGraph v0.8.27.1_STABLE

## Status

Stable recovery point.

`v0.8.27.1_RUNNER_POSIX_HARDENING_CANDIDATE` has been promoted after the full Windows Evidence CI run reported `Passed: True` on 2026-04-28.

## Stable scope

- Deterministic Governance Layer
- Enforcement as sole Gatekeeper
- Signed Capability Tokens with key rotation evidence
- Runtime Guard and Session Budget Guard
- Runtime Governance escalation states
- Cross-Session Budget Control via single-node Budget Ledger
- Budget Ledger reservation lifecycle
- Operational Hardening:
  - Budget snapshots
  - Audit replay consistency checks
  - Budget drift/anomaly detection
  - append-only incident records
- HTTP Policy Layer
- Secret references and delayed resolution
- External API Adapter controlled seam
- Audit / Explain reconstruction
- Pattern Engine proposal-only behavior
- Review Workflow and Controlled Apply Human-Gate
- Evidence Runner with POSIX timeout supervision patch and Windows selftest evidence

## Validation

Full Evidence CI reported:

```text
Passed: True
Unexpected Allows: 0
Invariant Violations: 0
```

Additional release-gate detail from `operational_hardening_evidence`:

```text
passed: 6
failed: 0
unexpected_allows: 0
invariant_violations: 0
```

## Production boundary

Still not production-ready for open distributed use. Remaining boundaries:

- Single-node only
- No production KMS
- No distributed budget lock/consensus
- Mock external API integration only
- No production monitoring/alerting stack
- No automated incident recovery

## Stable release document

See `docs/RELEASE_v0.8.27.1_STABLE.md`.
