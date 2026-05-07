# CI Evidence Runner (v0.8.7)

## Purpose

The CI evidence runner is a release-hygiene layer. It does not change governance, enforcement, budget, runtime, audit, explain, or pattern-engine semantics.

## Stabilization change

Earlier aggregate runs could hang in constrained Python environments after individual evidence scripts had already completed. The runner has therefore been hardened around two principles:

1. Each evidence script remains independently executable.
2. Aggregate CI treats runner failures/timeouts as explicit failed evidence, never as success.

## Runner options

- `tests/evidence_ci.py` keeps a machine-readable JSON summary format for evidence aggregation.
- `tests/evidence_ci.sh` provides a shell-isolated aggregate runner for CI environments where Python subprocess shutdown/pipe handling is unreliable.

## Invariants

- The runner may only orchestrate evidence.
- The runner may not weaken fail-closed behavior.
- The runner may not alter production code paths.
- A timeout or runner error is a failed release signal.

## Recommended CI command

```bash
./tests/evidence_ci.sh
```

The shell runner executes each test script with:

```bash
timeout 60 python -S -u <script>
```

This keeps the evidence process bounded and makes hangs visible as non-zero exit codes.
