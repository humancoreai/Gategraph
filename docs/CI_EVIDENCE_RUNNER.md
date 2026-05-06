# CI Evidence Runner

Version: v0.8.14 runner-harness-hardening

## Purpose

The CI evidence runner is a release-hygiene tool. It must not change production governance, enforcement, runtime, budget, secret, or HTTP policy semantics.

## Current strategy

`tests/evidence_ci.py` runs every evidence group as a separate process and records a JSON report under `tests/logs/`.

Important behavior:

- each evidence group gets a clean local `gategraph.db` slate
- output is file-backed to avoid pipe/capture deadlocks
- GNU `timeout` bounds every child process
- a timeout is accepted only if the child already emitted a zero-failure `Summary: {...}` line
- otherwise timeout is treated as failure

This separates real evidence failures from environment shutdown hangs.

## Invariant

The runner may classify evidence. It must never grant, block, mutate, or reinterpret production decisions.
