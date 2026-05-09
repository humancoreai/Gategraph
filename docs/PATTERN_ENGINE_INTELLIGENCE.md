# Pattern Engine Intelligence (v0.8.18)

## Purpose

The Pattern Engine now analyzes repeated audit evidence across multiple guard stages, not only repeated enforcement rejections.

It can observe recurring blocked patterns in:

- Enforcement
- HTTP Policy
- Secret Provider
- Session/Runtime guard stages when represented in API audit events

## Non-negotiable invariant

The Pattern Engine remains proposal-only.

It must never:

- activate or change rules
- widen HTTP allowlists
- raise budgets
- issue or revoke tokens
- change secret refs
- execute actions

All output is persisted as `pending_review` proposals.

## What changed

### Previous behavior

`analyze_rejections()` only considered `enforcement_rejection` events.

### New behavior

`analyze_audit_patterns()` scans audit events and extracts `PatternObservation` records for repeated blocked conditions.

It groups observations by:

- stage
- requested capability
- reason bucket

Only groups that meet both thresholds create proposals:

- `min_events`
- `confidence_threshold`

## Example proposal classes

### HTTP Policy

Repeated blocks for non-allowlisted endpoints generate a proposal to review caller configuration or endpoint policy.

The proposal explicitly says not to widen allowlists automatically.

### Secret Provider

Repeated secret resolution failures generate a proposal to review secret reference scope/provider setup.

The proposal explicitly says never to expose or log raw secret values.

### Enforcement

Repeated token/signature/task-binding failures generate a proposal to review token issuance flow or capability requests.

The proposal explicitly says not to auto-grant capabilities.

## Evidence

`tests/pattern_intelligence_evidence.py` verifies:

1. repeated HTTP Policy blocks create a proposal-only finding
2. repeated Secret Provider blocks create a proposal-only finding
3. mixed one-off failures do not overfit into a proposal
4. repeated invalid-token-signature evidence remains advisory and does not grant capabilities

## Boundary

This is not adaptive governance yet.

It is only an advisory pattern layer that prepares human-reviewable proposals from repeated audit evidence.
