# GateGraph v0.16.1_STABLE

Base: v0.16.0_STABLE
Status: stable
Version: 0.16.1

## Scope

This candidate hardens replay/recovery evidence, runtime/budget edge evidence, release-surface synchronization, and semantic-boundary preparation.

## Invariants

- Fail closed remains the default.
- Enforcement remains the only action gate.
- Replay/recovery surfaces are descriptive/reference-only.
- Semantic markers have no enforcement authority.
- No autonomous policy mutation, auto-repair, or auto-promotion is introduced.

## Candidate gate

Run on Windows:

```powershell
python tests\evidence_ci.py
```

Expected candidate result after local validation:

```text
CI EVIDENCE REPORT
Passed: True
```

## Known residual risks

- Candidate requires Windows Evidence CI before any stable promotion.
- Multi-node revocation remains out of scope.
- Semantic-boundary infrastructure is observability-only.


Phase: Evidence artifact hygiene and revocation negative-path hardening
