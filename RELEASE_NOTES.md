# Release Notes — GateGraph v0.11.8_STABLE

## Scope

Context Lifecycle / Freeze Coupling Baseline.

## Added

- Descriptive context lifecycle utility.
- Fail-closed lifecycle state and transition validation.
- Replay/explain/proposal rehydration blocking.
- Context lifecycle model documentation.
- Evidence for lifecycle boundaries, replay/explain non-executability and freeze coupling.

## Not changed

- No memory system.
- No vector database.
- No embeddings.
- No semantic scoring.
- No ML classifier.
- No autonomous context filtering.
- No adaptive trust system.
- No automatic poison detection claim.
- No AI content moderation.
- No governance logic changes.
- No runtime logic changes.
- No enforcement logic changes.
- No new agentic behavior.
- No distributed orchestration.
- No new adapter.
- No new token, budget, secret, or tool authority.

## Review hygiene fix

- README base-stable claim aligned with `v0.11.7_STABLE`.
- Canonical namespace boundary documented: `src/` remains runtime/governance surface; `gategraph/context/` remains bounded context-governance extension.
- Development STARTPROMPT artifacts excluded from release packaging.
- OWASP Agentic AI mapping surfaced from README.

