# Release Status - GateGraph v0.8.12-http-policy-allowlist

Status: Single-node PoC / governance kernel hardening.

## Added
- HTTP endpoint policy allowlist (`api_endpoint_policies`).
- Fail-closed blocking for non-HTTPS, unknown hosts, path mismatches, and method mismatches.
- HTTP policy audit metadata for external API calls.
- Evidence tests for allowlisted execution and blocked endpoint-policy violations.

## Unchanged
- Enforcement remains the only authorization gatekeeper.
- Guards still only stop, never allow.
- Secrets are still resolved only after all gates and HTTP policy pass.
- No real network client is shipped; transport remains an explicit seam.

## Known Limits
- No OS keychain/KMS.
- No real HTTP client policy stack beyond allowlist semantics.
- No distributed trust/budgeting.
- Aggregate runner remains environment-sensitive; individual evidence paths are preferred for local proof.
