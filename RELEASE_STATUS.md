# Release Status - GateGraph v0.8.17-block-e-documentation-reality-check

Status: Single-node PoC / documentation reality check.

## Added
- `docs/BLOCK_E_DOCUMENTATION_REALITY.md`.
- Explicit current-limitations section in README.
- Updated SECURITY framing for implemented PoC controls vs. production gaps.

## Corrected
- Removed obsolete claims that token signing is not implemented.
- Removed obsolete claims that runtime/cost-control layer is absent.
- Removed obsolete claims that external API integration is absent; it is now documented as controlled/policy-gated PoC integration.
- Version labels aligned to v0.8.17.

## Unchanged
- Enforcement remains the only authorization gatekeeper.
- Guards still only stop, never allow.
- HTTP Policy and Secret Provider order is unchanged.
- Trace building remains read-only.
- Production governance/enforcement/runtime semantics unchanged.

## Evidence
- Block E is documentation-only.
- Syntax/compile check remains the relevant technical sanity check.
- Existing Block C/D and security evidence remain applicable from v0.8.16/v0.8.15/v0.8.14.

## Known Limits
- GateGraph remains a Single-Node SQLite PoC.
- No KMS/OS-keychain lifecycle.
- No distributed trust/budget model.
- No unrestricted production HTTP/API execution.
- Aggregate runner remains environment-sensitive in local runs.
