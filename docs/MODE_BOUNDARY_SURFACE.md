# Mode Boundary Surface – GateGraph v0.11.4_CANDIDATE

Status: stable
Base: v0.11.3_STABLE
Phase: Capability Token Audit Redaction

## Purpose

This document freezes the mode boundary as a descriptive governance surface. It does
not introduce a new runtime mode, adapter behavior, governance authority, policy
engine, tool permission, distributed execution model, cloud deployment layer, or UI.

## Boundary invariant

Modes may only narrow, label, or clarify an already-governed execution context. A
mode must never expand authority beyond the central governance decision, capability
token, guard chain, configured budgets, HTTP policy, secret scope, or human review
requirements.

## Allowed descriptive mode classes

The architectural labels from `docs/MULTI_MODE_SSOT.md` remain descriptive only:

- `observer`: read-only observation; no external side effects
- `worker`: governed execution under existing guard and token constraints
- `reviewer`: proposal/findings only; no enforcement authority
- `blocked`: explicit fail-closed state

## Forbidden mode claims

A release must not claim that modes provide:

- autonomous policy changes
- hidden execution rights
- self-selected privilege escalation
- budget expansion
- unreviewed tool access
- governance bypass
- direct secret access
- adapter-side governance decisions
- distributed or multi-node orchestration

## Evidence coupling

Mode boundary claims are acceptable only when these surfaces agree:

| Surface | Source of truth |
|---|---|
| Mode SSOT | `docs/MULTI_MODE_SSOT.md` |
| Mode boundary | `docs/MODE_BOUNDARY_SURFACE.md` |
| Runtime surface | `docs/RUNTIME_SURFACE_FREEZE.md` |
| Operational non-scope | `docs/OPERATIONAL_BOUNDARY_TIGHTENING.md` |
| Release metadata | `RELEASE_METADATA.json` |
| Evidence CI | `tests/evidence_ci.py` |

Any claim that converts modes into authority is release drift and must fail evidence.
