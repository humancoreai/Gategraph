# Human Review Queue (v0.8.43)

## Purpose

The Human Review Queue provides a structured reference list for human operator review.
It connects incidents, failure patterns and playbooks to a human-visible queue without
changing GateGraph decisions or runtime behavior.

## Invariants

- Append-only documentation only.
- No automatic reactions.
- No Governance, Enforcement, Runtime, Budget or Audit mutation.
- No ranking, scoring, severity, recommendation or hidden triage semantics.
- Queue order is append order only and has no evaluation meaning.

## Data Surfaces

- `operator_logs/human_review_queue.jsonl`
- `operator_logs/human_review_activity.jsonl`

Both logs are runtime documentation artifacts and are ignored by repository hygiene.

## Allowed Operations

- Append a review reference item.
- Read review items in append order.
- Filter by stable references such as task, incident, pattern or playbook id.
- Append human review activity as documentation only.
- Create a reproducible reference snapshot.

## Explicit Non-Scope

- Approval or rejection workflows.
- Automatic escalation.
- Policy tuning.
- Rule updates.
- Root-cause analysis.
- Any evaluation of urgency or rank.
