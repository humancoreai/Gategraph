# Evidence Runtime Profiles

Release: v0.17.7_CANDIDATE  
Base: v0.17.3_STABLE  
Status: candidate

This document defines scoped evidence execution profiles for operator ergonomics.

The full Windows Evidence CI remains the authoritative validation path before Stable promotion. Profiles are descriptive execution bundles only. They do not remove tests, demote mandatory gates, bypass fail-closed checks, or change governance/runtime behavior.

## Profiles

- `release_fast`: release, version, registry-lock and promotion-gate checks.
- `core_runtime`: runtime, session, orchestration and operational stability checks.
- `security_boundary`: token, secret, HTTP and redaction boundary checks.
- `full_ci`: unchanged full `python tests/evidence_ci.py` validation path.

## Non-authority guarantees

- no automatic pruning
- no automatic repair
- no automatic promotion
- no policy mutation
- no runtime authority
- no enforcement change

## Intent

The purpose is to make repeated local validation less noisy while preserving the full evidence chain for Candidate and Stable gates.
