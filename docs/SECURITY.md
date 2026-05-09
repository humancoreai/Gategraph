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

## 4. Known security limits

These are acceptable for the PoC but must be addressed before production use:

- tokens are not cryptographically signed
- no external identity model
- no reviewer trust model
- no concurrency/race-condition hardening
- no runtime/cost-control layer
- no sandboxed tool runtime

---

## 5. Security recommendation before production

Before production use, add:

1. HMAC or signed capability tokens
2. dedicated approval workflow
3. concurrency controls
4. runtime/cost-control layer
5. tool sandboxing
6. formal revocation cache or low-latency revocation check
