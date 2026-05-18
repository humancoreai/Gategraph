# Release Notes – v0.17.6_STABLE

Base: v0.17.6_STABLE  
Status: stable  
Version: 0.17.4  
Phase: Evidence artifact hygiene and revocation negative-path hardening  
Release focus: Evidence Artifact Hygiene / Revocation Negative Path Hardening

## Summary

v0.17.6_STABLE closes the stale-token window found during practical controlled-apply testing. When a rule is hardened through controlled apply, active non-expired capability tokens whose issuing decision depended on that rule are revoked.

## Changes

- Added `revoke_active_tokens_for_rule()` to mark dependent active tokens as revoked after controlled rule updates.
- Updated `execute_apply_artifact()` to revoke affected tokens after successful rule hardening.
- Extended `controlled_apply_evidence` with stale-token proof: token issued before rule change → rule hardened → token revoked → enforcement rejects token.
- Preserved existing enforcement semantics: revoked tokens are rejected through the existing DB-backed enforcement check.

## Non-scope

- No distributed governance.
- No new runtime model.
- No new risk model.
- No automatic policy mutation.
- No production keyring overhaul in this stable release.

## Compatibility Notes

v0.17.6_STABLE is based on v0.17.6_STABLE and keeps the single-node local protected deployment boundary unchanged.
