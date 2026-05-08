# Capability Token Key Management (v0.8.9)

## Scope

GateGraph now supports explicit HMAC key IDs for Capability Token signing.

This is still a Single-Node implementation. It is not distributed trust, not asymmetric signing, and not a production secret-management system.

## Behavior

- New tokens are signed with `GATEGRAPH_TOKEN_ACTIVE_KEY_ID`.
- Verification uses `GATEGRAPH_TOKEN_KEYRING_JSON`.
- Old tokens remain valid only while their `signing_key_id` is still present in the trusted keyring.
- Unknown key IDs fail closed at Enforcement.
- Signing-key-ID tampering fails closed through claim mismatch / signature validation.

## Environment

```text
GATEGRAPH_TOKEN_ACTIVE_KEY_ID=rot-v2
GATEGRAPH_TOKEN_KEYRING_JSON={"rot-v2":"secret-v2","rot-v1":"secret-v1"}
```

Compatibility path:

```text
GATEGRAPH_TOKEN_SIGNING_SECRET=single-secret
GATEGRAPH_TOKEN_ACTIVE_KEY_ID=local-prod-v1
```

## Rotation Procedure

1. Add the new key to the keyring.
2. Set `GATEGRAPH_TOKEN_ACTIVE_KEY_ID` to the new key.
3. Keep the previous key in the keyring until old tokens expire or are revoked.
4. Remove the previous key from the keyring after its trust window ends.

## Invariants

- Enforcement never accepts tokens signed by unknown keys.
- Rotation does not grant new capabilities.
- Rotation does not bypass revocation, expiry, task binding, or persisted-claim checks.
- Key management is verification-only at runtime; Pattern Engine remains proposal-only.
