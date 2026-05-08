# CI Evidence Runner

Version: v0.8.23 evidence-runner-stabilization

## Purpose

The CI evidence runner is a release-hygiene tool. It must not change production governance, enforcement, runtime, budget, secret, HTTP policy, review, or controlled-apply semantics.

## Current strategy

`tests/evidence_ci.py` runs every evidence group as a separate bounded subprocess and records a JSON report under `tests/logs/`.

Each script is executed through `tests/_run_isolated.py` instead of being launched directly. The wrapper imports the evidence module, calls its public `main()` or `run()` entrypoint, then hard-exits with the returned code.

This avoids environment-specific interpreter shutdown hangs while preserving the evidence script behavior itself.

Important behavior:

- each evidence group gets a clean local `gategraph.db` slate
- output is file-backed to avoid pipe/capture deadlocks
- GNU `timeout` bounds every child process
- a timeout is accepted only if the child already emitted a zero-failure `Summary: {...}` line
- otherwise timeout is treated as failure
- Controlled Apply evidence is included in the aggregate manifest

## Compatibility entrypoint

`tests/evidence_supervisor.py` is retained as a compatibility wrapper and delegates to `tests/evidence_ci.py`. The previous multiprocessing supervisor path is intentionally removed because it could hang during child process shutdown in this environment.

## Invariant

The runner may classify evidence. It must never grant, block, mutate, or reinterpret production decisions.
