# GateGraph Test Report — v0.5 PoC

## 1. Test scope

Three simulation phases were executed:

1. Normal usage simulation
2. Unusual input simulation
3. Agent scenario simulation

The goal was not performance testing. The goal was invariant validation.

---

## 2. Normal usage simulation

Summary:

```text
Runs: 10
Unexpected allows: 0
Invariant violations: 0
```

Covered:

- local file reads
- local source reads
- write attempts
- delete attempts
- untrusted document read
- secret config read
- external API call
- unknown action

Result:

```text
passed
```

---

## 3. Unusual input simulation

Summary:

```text
Runs: 12
Unsafe allows: 0
Invariant violations: 0
```

Covered:

- empty capabilities
- unknown capability
- mixed read/write request
- duplicate capabilities
- case mismatch
- empty input source
- unknown input source
- unknown sensitivity
- secret + untrusted
- secrets + unknown capability
- uppercase external input source
- very long capability name

Result:

```text
passed
```

---

## 4. Agent scenario simulation

Summary:

```text
Runs: 12
Unexpected allows: 0
Invariant violations: 0
```

Covered:

- agent reads repo files
- agent proposes patch
- agent attempts direct write
- agent attempts delete
- agent reads untrusted document
- agent follows untrusted write instruction
- agent handles secret config
- agent external API call
- unknown tool request
- mixed read/write request
- prompt-injection-like untrusted read

Result:

```text
passed
```

---

## 5. Current interpretation

GateGraph v0.5 successfully validates:

```text
- no write without approval
- no delete without approval
- no external API execution
- no unknown tool execution
- no critical-risk execution
- no cross-task token reuse
- no revoked-token execution
- no unsafe allows in tested flows
```

---

## 6. Remaining non-test gaps

The following are not test failures but future work:

- runtime/cost control
- pattern engine
- token signing
- production concurrency
- real approval workflow
- graph query API
