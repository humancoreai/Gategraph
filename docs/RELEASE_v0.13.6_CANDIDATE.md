# GateGraph v0.13.6_CANDIDATE Release

Status: candidate.  
Base: v0.13.5_STABLE.

## Scope

GitHub Actions CI Preparation.

This candidate adds a minimal, deterministic GitHub Actions validation surface for Windows Evidence CI. It does not change governance, runtime, enforcement, risk, token, recovery, replay, registry, or operator logic.

## Added surfaces

- `.github/workflows/evidence_ci.yml`
- `docs/GITHUB_ACTIONS_CI.md`
- `tests/github_actions_ci_evidence.py`

## Invariants

- CI is evidence-only.
- CI has read-only repository permissions.
- CI does not access secrets.
- CI does not publish packages.
- CI does not deploy.
- CI does not promote Candidate to Stable.
- Stable promotion still requires explicit Candidate CI evidence with `Passed: True`.

## Non-scope

- No automatic release authority.
- No cloud-only production requirement.
- No replacement of local Windows Evidence CI.
- No governance mutation or auto-repair.
