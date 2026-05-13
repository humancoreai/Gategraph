# Practical Single-Node Scenario

Release: v0.16.1_CANDIDATE  
Base: v0.14.7_STABLE  
Status: candidate

## Scope

This document defines a small, deterministic single-node scenario run for local validation.
It is intentionally narrower than a production pilot and does not introduce new governance,
runtime, enforcement, policy-learning, deployment, or self-orchestration behavior.

## Scenario boundary

The scenario exercises the existing single-node adapter path with mixed realistic inputs:

- benign local read
- untrusted read containing prompt-injection text
- fake operator/system claims supplied as data
- unknown/admin capability request
- local write request
- secret-involved read request
- monitoring export read-only check

## Invariants

- The service adapter remains the only public entry path.
- Caller-supplied text is treated as data, not authority.
- Unknown capabilities fail closed.
- Write/delete/API capabilities are not granted by prompt-injection text.
- Monitoring export remains read-only and does not mutate core counts.
- No automatic repair, promotion, deployment, or policy mutation is performed.

## Non-scope

This is not a load test, not a production deployment, not an autonomous red-team harness,
and not a permanent replay of the ad-hoc stress simulation report.
