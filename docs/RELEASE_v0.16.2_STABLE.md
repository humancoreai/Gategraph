# GateGraph v0.16.8_CANDIDATE

Base: v0.16.8_CANDIDATE
Status: stable
Version: 0.16.8

## Scope

This candidate hardens promotion-pipeline status-token evidence. It specifically prevents VERSION.md from passing release/base checks while silently missing the active candidate/stable status token.

## Invariants

- Fail closed remains the default.
- Enforcement remains the only action gate.
- Release-surface checks are descriptive only and add no promotion authority.
- VERSION.md must carry explicit release, base, status and version tokens.
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


Phase: Evidence Maintainability Hardening
