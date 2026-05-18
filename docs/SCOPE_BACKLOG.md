# GateGraph Scope Backlog

Release: v0.16.8_STABLE
Base: v0.16.7_STABLE
Status: stable
Version: 0.16.8
Phase: Release Status Assertion Policy
Release focus: Release Status Assertion Policy

## Purpose

This document separates current scope from deferred scope so that public documentation does not imply delivery promises.

## Current Scope

GateGraph currently targets local, protected, single-node governance evaluation and evidence-based release validation.

In scope now:
- local CLI evaluation
- local protected HTTP adapter
- deterministic governance/evidence checks
- append-only audit semantics
- release surface consistency
- public review readiness

## Deferred Scope

| Item | Status | Earliest scope condition |
|---|---|---|
| Auth/TLS built into GateGraph | Deferred | After local practical tests show stable adapter semantics |
| KMS / managed secret backend | Deferred | After signing-key lifecycle is specified and externally reviewed |
| Multi-node governance | Deferred | After single-node practical tests and replay semantics are stable |
| External agent-framework integration | Deferred | After local mini-agent scenarios are reproducible |
| Customer-system assessment agent | Deferred | After read-only assessment model and proposal-only boundary are specified |
| Public internet deployment | Out of current scope | Only after authentication, TLS, rate limiting, deployment hardening and threat-model review |

## Scope Rule

Deferred items may enter scope only through a future Candidate with:
- explicit release metadata scope flag,
- documentation update,
- evidence test,
- no silent runtime authority expansion,
- human approval before Stable promotion.

