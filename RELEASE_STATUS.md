# Release Status - GateGraph v0.8.13-security-finesse

Status: Single-node PoC / security-finesse hardening.

## Added
- `tests/security_finesse_evidence.py` with focused Block B checks:
  - secret value does not appear in audit/evidence,
  - HTTP policy denial prevents secret resolution,
  - subdomains are not implicitly allowed,
  - wildcard host policies are rejected,
  - path-prefix boundaries block `/v10` when only `/v1` is allowed,
  - lowercase HTTP methods normalize correctly,
  - expired+revoked tokens stay fail-closed with deterministic expiry-first reason.

## Changed
- HTTP policy path matching is boundary-aware.
- Endpoint policy registration rejects wildcard hosts.
- Evidence CI script includes the new security-finesse evidence group.

## Unchanged
- Enforcement remains the only authorization gatekeeper.
- Guards still only stop, never allow.
- Secrets are resolved only after Enforcement, Session Budget, Runtime Guard, and HTTP Policy pass.
- No real network client is shipped; transport remains an explicit seam.

## Known Limits
- No OS keychain/KMS.
- No real HTTP client policy stack beyond allowlist semantics.
- No distributed trust/budgeting.
- Aggregate runner remains environment-sensitive; individual evidence paths are preferred for local proof.
