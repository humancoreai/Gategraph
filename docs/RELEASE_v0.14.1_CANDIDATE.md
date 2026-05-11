# GateGraph v0.14.1_CANDIDATE

Base: v0.14.0_STABLE  
Status: candidate  
Phase: Install / Packaging / Public Repo Hygiene

## Purpose

This candidate focuses on install, packaging and public repository hygiene after the practical single-node scenario baseline.

## Scope

- Public-repo hygiene documentation.
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
- existing release, manifest, surface, packaging and CI evidence gates

## Promotion gate

Stable promotion requires Windows Evidence CI `Passed: True` for `v0.14.1_CANDIDATE`.
