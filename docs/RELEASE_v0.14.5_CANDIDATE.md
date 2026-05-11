# GateGraph v0.14.5_CANDIDATE

Base: v0.14.4_STABLE  
Status: candidate  
Phase: Install / Packaging / Public Repo Hygiene

## Purpose

This candidate focuses on fresh-clone reproducibility, dependency/onboarding hygiene and public repository verification after v0.14.1 candidate public-repo hygiene.

## Scope

- Fresh-clone reproducibility documentation.
- Dependency and onboarding surface consistency.
- Quickstart surface for reproducible local verification.
- Evidence coverage for packaging/public-facing repository hygiene.
- Release/manifest/version consistency for the candidate.

## Non-scope

- No new governance logic.
- No runtime authority changes.
- No policy mutation or automatic promotion.
- No new agentic behavior.
- No production deployment claim.

## Evidence

- `tests/public_repo_hygiene_evidence.py`
- `tests/fresh_clone_reproducibility_evidence.py`
- existing release, manifest, surface, packaging and CI evidence gates

## Promotion gate

Candidate promotion requires Windows Evidence CI `Passed: True` for `v0.14.5_CANDIDATE`.


## v0.14.5 Candidate Scope

- GitHub Actions runtime stress determinism hardening.
- CI profile for runtime stress micro-flood evidence to avoid hosted-runner timeout drift.
- No governance logic change, no runtime authority expansion, no auto-promotion.
