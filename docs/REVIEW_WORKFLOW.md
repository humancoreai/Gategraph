# Review Workflow (v0.8.21)

The Review Workflow adds an explicit human/process gate for Pattern Engine proposals.

## Purpose

Pattern Engine output is advisory. The Review Workflow lets a reviewer mark a proposal as:

- `approved_for_manual_action`
- `rejected`

Approval does **not** apply any runtime change. It only records that a human/process reviewer accepted the proposal as worth manual follow-up.

## Invariants

- Pattern Engine does not decide.
- Review approval does not change rules.
- Review approval does not change HTTP policies.
- Review approval does not change budgets.
- Review approval does not grant capabilities or tokens.
- Review approval does not expose or mutate secrets.
- Review approval does not execute actions.

## Why approval is intentionally named `approved_for_manual_action`

The name avoids a dangerous ambiguity: approval is not application.

A future controlled-apply mechanism, if added, must be a separate gate with its own invariants, evidence, audit trail, and human authorization model.
