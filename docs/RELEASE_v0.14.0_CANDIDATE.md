# GateGraph v0.14.0_CANDIDATE Release

Status: candidate.  
Base: v0.13.6_STABLE.

## Scope

Practical Single-Node Scenario Run.

This stable release preserves a minimal, deterministic GitHub Actions validation surface for Windows Evidence CI. It does not change governance, runtime, enforcement, risk, token, recovery, replay, registry, or operator logic.

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


## Practical scenario scope

Practical single-node scenario evidence validates the existing service-adapter path with benign, prompt-injection-like, unknown-capability, write, secret and monitoring-export cases. The ad-hoc stress simulation report remains external and is not part of this release.
