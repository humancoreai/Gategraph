# CI Evidence Runner

Version: v0.8.14 runner stabilization

## Purpose

The Evidence Runner is the release proof harness for GateGraph. It executes all proof-oriented test scripts and writes one machine-readable JSON summary under `tests/logs/`.

## Current runner model

`tests/evidence_ci.sh` is the preferred aggregate runner.

It executes each evidence script through:

```bash
python -S -u tests/_run_isolated.py <script>
```

`_run_isolated.py` imports the target script as a normal module and calls its public `main()` or `run()` function directly.

## Why not `runpy(..., run_name="__main__")`?

Earlier runner versions executed scripts as `__main__`. In this environment that could produce shutdown hangs after the logical test result was already printed. The v0.8.14 wrapper avoids that path and exits after explicit stream flushing.

## Invariant

The runner only orchestrates tests. It does not change production semantics in:

- Governance
- Enforcement
- Runtime Guard
- Session Budget Guard
- HTTP Policy
- Secret Provider
- External API Adapter
- Pattern Engine

## Expected result

A clean run prints one line per evidence group and then a final report:

```text
CI EVIDENCE REPORT
Log: tests/logs/ci_evidence_<timestamp>.json
Passed: true
```

## Notes

Output tails are base64-encoded in the JSON report so arbitrary test output cannot corrupt the machine-readable summary.
