# Pattern Clustering (v0.8.20)

Pattern clustering compresses repeated Pattern Engine proposals into reviewer-friendly groups.

## Scope

- Groups advisory proposals by proposal type and inferred target.
- Aggregates support, score, priority and representative examples.
- Produces plain review data for dashboards or human review.

## Non-goals / invariants

- Does not change rules.
- Does not alter HTTP policies.
- Does not read or alter secrets.
- Does not grant tokens or capabilities.
- Does not approve proposals.
- Does not execute actions.

Pattern clustering improves triage only. It is not an apply mechanism.
