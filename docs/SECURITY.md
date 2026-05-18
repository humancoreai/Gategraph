# Security Notes — v0.17.9_STABLE

Current public security surface: `v0.17.9_STABLE`. Base: `v0.17.9_STABLE`.

# GateGraph Security Notes

## 1. Security posture

GateGraph follows a fail-closed model.

If a request is unknown, ambiguous, expired, revoked, or lacks a valid token, enforcement blocks.

---

## 2. Core security invariants

```text
INV-001: No tool action without capability token.
INV-002: Missing capability defaults to deny.
INV-003: Expired tokens are blocked.
INV-004: Revoked tokens are blocked.
INV-005: Tokens are task-bound.
INV-006: Critical risk never receives automatic execution permission.
INV-007: Untrusted input is data, not instruction.
INV-008: Events are append-only.
```

---

## 3. Threat model

### 3.1 Direct write attempt

Risk:

```text
Agent tries to write files directly.
```

Mitigation:

```text
write_files → high risk → require_approval → no token → enforcement blocks
```

---

### 3.2 Delete attempt

Risk:

```text
Agent tries to delete files.
```

Mitigation:

```text
delete_files → high risk → require_approval → no token → enforcement blocks
```

---

### 3.3 Prompt injection in document

Risk:

```text
Untrusted document instructs agent to ignore rules or perform writes.
```

Mitigation:

```text
input_source=untrusted → medium risk → require_review
read-only analysis may proceed
side effects remain blocked
```

---

### 3.4 Secret exposure

Risk:

```text
Task touches secrets or secret-classified data.
```

Mitigation:

```text
secrets_involved=true or data_sensitivity=secret → critical → require_approval
no automatic execution token
```

---

### 3.5 Token reuse across tasks

Risk:

```text
Valid token from Task A used on Task B.
```

Mitigation:

```text
enforcement checks token.task_id == requested task_id
```

---

### 3.6 Revoked token

Risk:

```text
Previously issued token is revoked but still used.
```

Mitigation:

```text
enforcement queries token revocation state before allowing
```

---

## 4. Current PoC security controls

Implemented at Single-Node PoC level:

- HMAC-signed Capability Tokens over immutable claims
- explicit signing key IDs and local keyring verification
- task-bound token enforcement and cross-task replay blocking
- revocation and expiry checks during enforcement
- Runtime Guard for per-task loops, steps, and runtime cost
- Session Budget Guard for global and agent-level cost limits
- HTTP Policy allowlist for scheme, host, path boundary, and method
- scoped secret references resolved only after Enforcement, Budget, Runtime, and HTTP Policy pass
- append-only audit events and read-only explain trace reconstruction

---

## 5. Known security limits

These are acceptable for the PoC but must be addressed before production use:

- no external identity model
- no reviewer trust / human approval model
- no KMS or OS-keychain integration; current secret resolution is env-backed
- no asymmetric signatures or distributed trust boundary
- no multi-node/distributed budget coordination
- no sandboxed tool runtime
- no production billing integration, alerting, or incident workflow
- aggregate evidence runner remains environment-sensitive in local runs

---

## 6. Security recommendation before production

Before production use, add:

1. managed secret storage (OS keychain/KMS) and rotation lifecycle
2. dedicated approval workflow and reviewer trust model
3. distributed concurrency / budget coordination if crossing process or node boundaries
4. sandboxed tool runtime
5. formal revocation cache or low-latency revocation check
6. operational monitoring, billing integration, and alerting

## Capability Token integrity (v0.8.8)

Capability Tokens now include HMAC signatures over immutable claims. Enforcement validates persisted claims and signature before it grants a capability. Any mismatch fails closed.

Boundary: the current signing model is local/symmetric. Key ID based local rotation is implemented at PoC level; production-style distributed trust and asymmetric verification remain out of scope.
