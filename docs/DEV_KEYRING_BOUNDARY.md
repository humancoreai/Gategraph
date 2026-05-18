# Development Keyring Boundary

Release: `v0.17.9_CANDIDATE`
Base: `v0.17.8_STABLE`
Status: candidate

GateGraph does not silently fall back to the deterministic development signing keyring.

Accepted signing-key sources:

1. `GATEGRAPH_TOKEN_KEYRING_JSON`
2. `GATEGRAPH_TOKEN_SIGNING_SECRET`
3. development keyring only when `GATEGRAPH_ALLOW_DEV_KEYRING=1`

This is a fail-closed default. Local evidence and examples may opt in explicitly.

No runtime authority is added by this boundary.
