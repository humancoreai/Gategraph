# GateGraph v0.8.27.1_STABLE

## Status

Stable recovery point after Operational Hardening and Evidence Runner POSIX hardening.

Promoted from `v0.8.27.1_RUNNER_POSIX_HARDENING_STABLE` after the full Windows Evidence CI run reported `Passed: True` on 2026-04-28.

## Consolidated scope

- Deterministic Governance remains the only decision authority.
- Enforcement remains the sole token gatekeeper.
- Runtime and Session guards only stop; they do not allow.
- Budget authority remains in Governance and the Budget Ledger.
- Operational Hardening adds observation and consistency checks, not new autonomy.
- Evidence Runner POSIX timeout handling is hardened without changing production logic.

## Operational Hardening

Included stable capabilities:

- Budget snapshots across ledger scopes.
- Deterministic audit replay consistency reports.
- Budget overspend and state-drift anomaly detection.
- Append-only operational incident records.

## Evidence

Full Evidence CI:

```text
Passed: True
Unexpected Allows: 0
Invariant Violations: 0
```

Operational Hardening evidence:

```text
passed: 6
failed: 0
unexpected_allows: 0
invariant_violations: 0
```

Evidence runner selftest:

```text
passed: 3
failed: 0
timeout_script: timeout, killed_process_group: true
```

## Repo hygiene

- Generated Python caches removed.
- Compiled Python files removed.
- Generated evidence logs removed.
- `tests/logs/.gitkeep` retained.
- Version, release status, release notes and README updated.

## Known limits

- Single-node only.
- No production KMS.
- No distributed budget lock/consensus.
- Mock external API integration only.
- No production monitoring/alerting stack.
- No automated incident recovery.
- POSIX runner patch is structurally hardened, but the supplied full release-gate evidence was executed on Windows.

## Decision

`v0.8.27.1_STABLE` is suitable as the next stable recovery point.
