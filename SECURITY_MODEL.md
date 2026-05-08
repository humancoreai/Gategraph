# GateGraph Security Model – v0.11.7_CANDIDATE

GateGraph is a deterministic governance and enforcement boundary for agentic task execution. It is not an agent, not a sandbox, and not a distributed security platform.

## Layer model

### Governance layer
The governance layer evaluates a task, applies the configured rules, and records a decision. It does not execute side effects. Capability tokens are issued only from allowed decisions and remain bound to their task and decision context.

### Enforcement layer
The enforcement layer is the only action gate. A requested action must present a valid, non-expired, non-revoked, correctly signed capability token with matching claims. Enforcement does not re-run governance policy.

### Runtime layer
Runtime guards bound per-task execution by step count, runtime, repeated action signatures, and cost units. Runtime controls do not grant authority; they only stop or allow continuation inside an already authorized path.

### Session and budget layer
Session, actor, task, and broader budget scopes are used to reduce split-task, flood, and runaway-cost behavior. Budget governance is fail-closed when required scopes are missing or inconsistent.

### HTTP policy layer
Outbound HTTP-style integrations are denied unless an explicit HTTPS host/path/method policy allows the endpoint. Policy evaluation occurs before secret resolution and before transport execution.

### Secret resolution boundary
Secrets are referenced by `secret_ref_id`. Raw secret values are resolved only after enforcement, budget, runtime, and HTTP policy checks pass. Secret values are passed only to the transport boundary and are not stored in audit, explain, monitoring, or evidence payloads.

### Capability token lifecycle
Capability tokens are signed, scoped, expiring, revocable, and task-bound. Reviewer-facing outputs may contain only:

- `token_id`
- `token_hash`
- `key_id` / `kid`

Raw tokens, signatures, signing input, Authorization headers, bearer payloads, and base64-encoded token material are not audit-safe.

### Explain and audit boundary
Audit, explain, monitoring, and operator-facing exports are descriptive. They must not become a covert channel for sensitive material. v0.11.7 adds centralized redaction and evidence for token, Authorization header, and secret exposure boundaries.

## Trust boundaries

| Boundary | Trusted input | Untrusted / constrained input | Rule |
|---|---|---|---|
| Task request | service adapter entry context | task payload, input source | fail closed on invalid entry |
| Capability token | signed claims | raw bearer/token material | never log raw token material |
| HTTP endpoint | allowlisted host/path/method | arbitrary URL | deny by default |
| Secret | configured secret ref | secret value | resolve only after all gates |
| Explain/export | persisted audit state | sensitive payload fields | redacted descriptive view only |

## Non-claims

GateGraph v0.11.7 does not provide kernel isolation, full runtime sandboxing, distributed Byzantine tolerance, autonomous threat hunting, complete memory governance, or guaranteed protection against unknown future agent strategies.
