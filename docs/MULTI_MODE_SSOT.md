# Multi-Mode SSOT — v0.9.2_STABLE

## Status

Modes are descriptive profiles. They do not create new authority.

## Mode Definition

A Mode is a named constraint profile applied to a governed task or agent context.

A mode may describe:

- runtime_profile: step, loop, timeout, and cost limits
- capability_profile: allowed tools/actions/endpoints
- safety_level: stricter guard thresholds
- explainability_level: required trace detail
- isolation_level: allowed communication and state access
- human_gate_level: review requirement before execution

## Mode Invariant

A mode can only narrow or clarify permissions. A mode cannot expand authority beyond central governance decisions.

## Forbidden Mode Semantics

A mode must not imply:

- autonomous policy changes
- hidden execution rights
- self-selected privilege escalation
- budget expansion
- unreviewed tool access
- governance bypass

## Initial Mode Classes

- observer: read-only, no external side effects
- worker: governed execution under narrowed capability token
- reviewer: proposes findings, no enforcement authority
- blocked: explicit fail-closed state

These classes are architectural labels only in v0.9.2_STABLE.
