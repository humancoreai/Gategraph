# Context Governance Model — v0.17.4_STABLE

## Scope

This release treats context as an explicit security and governance boundary.

It does not implement memory, vector search, semantic scoring, autonomous content moderation, adaptive trust, or an agent memory system.

## Core invariant

Context does not create authority.

A context object may describe a request, prior decision, replay record, proposal, external response, operator note, or runtime state. It must not implicitly grant rights, mutate governance, create capability tokens, change runtime limits, or become executable because the text is phrased as an instruction.

## Context types

| Context type | Trust level | Governance influence | Executable | Replayable | Intended use |
|---|---:|---:|---:|---:|---|
| `trusted_system_context` | trusted | true | false | false | Static trusted system configuration or governance source material. |
| `trusted_operator_context` | trusted | false | false | true | Operator-visible notes or input that remain separate from policy mutation. |
| `untrusted_external_context` | untrusted | false | false | true | External API content, user-supplied text, web content, logs, imported text. |
| `transient_runtime_context` | runtime | false | false | false | Ephemeral runtime state for observation; not a policy channel. |
| `replay_context` | reference | false | false | true | Historical replay/audit/explain context. Descriptive only. |
| `proposal_context` | proposal | false | false | true | Human-reviewable proposal text. Non-authoritative until explicitly accepted through a separate governance process. |

## Provenance requirements

Every classified context object must carry explicit provenance:

```json
{
  "context_type": "untrusted_external_context",
  "source": "external_api",
  "trust_level": "untrusted",
  "governance_influence": false,
  "executable": false,
  "replayable": true
}
```

There are no implicit defaults. Missing source, unknown context type, missing provenance fields, or inconsistent trust metadata fail closed.

## Instruction / data separation

Instruction-like text inside context remains data unless it enters through a trusted, explicit governance path.

Examples that remain data inside untrusted/replay/proposal context:

- `ignore previous instructions`
- `operator approved`
- `grant capability`
- `change policy`
- `delegate this to another agent`
- embedded fake system prompts

The boundary layer may mark suspicious patterns for audit and explainability. It does not autonomously block, moderate, score, or interpret semantic intent.

## Explain and replay semantics

Replay, explain and snapshot context is marked as:

- `descriptive_only`
- `non_executable`
- `reference_context`

Replay and explain material must not become runtime input, mutate policy, produce delegation, or create a capability token. It is only a reference representation of historical or explanatory material.

## Fail-closed conditions

GateGraph fails closed when:

- context type is unknown
- provenance is missing
- source is missing
- trust level is inconsistent with the context type
- executable context is presented where a data context is required
- governance influence is claimed by untrusted, replay, or proposal context

## System limits

v0.11.9 does not claim to detect all prompt injection, context poisoning, fake authority claims, or semantic manipulation. It only establishes deterministic structural boundaries so that such text cannot become authority by being included as context.


## Release hygiene note

This document is carried forward for v0.17.4_STABLE as the current context-governance boundary reference.
The version bump is formal documentation hygiene only; it does not introduce memory, semantic scoring,
runtime authority, policy mutation, or enforcement behavior.

Base reference: v0.17.4_STABLE.
