# Capability Token Hardening (v0.8.8)

## Purpose

Capability Tokens are now integrity-protected with an HMAC signature over immutable token claims.

## Bound Claims

The signature covers:

- `token_id`
- `decision_id`
- `task_id`
- sorted `capabilities`
- `issued_at`
- `expires_at`
- `signing_key_id`

## Enforcement Behavior

Enforcement still remains the only gatekeeper. Before allowing an action, it now checks:

1. token exists
2. token is bound to the requested task
3. token is not expired
4. token is present in persistence
5. token is not revoked
6. persisted claims match the presented token
7. signature is valid
8. requested capability is granted

Any mismatch fails closed.

## Secret Handling

The signing secret is read from `GATEGRAPH_TOKEN_SIGNING_SECRET`.

For local deterministic tests only, a fixed development fallback is used. This is not a production boundary.

## Scope Boundary

This release does not add:

- distributed key management
- key rotation
- asymmetric signatures
- external trust delegation

Those remain later hardening steps.
