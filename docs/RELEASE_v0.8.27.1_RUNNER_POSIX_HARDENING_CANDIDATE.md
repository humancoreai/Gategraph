# Release Candidate: v0.8.27.1_RUNNER_POSIX_HARDENING_STABLE

## Classification

Patch release candidate.

## Scope

Evidence Runner hardening only.

## Changed

- POSIX path migrated from external `timeout` wrapper to Python-owned `Popen` supervision.
- POSIX child process now starts in an isolated session via `start_new_session=True`.
- Timeout handling is aligned with the Windows runner model.
- Existing file-backed stdout/stderr behavior is preserved.

## Not changed

- Governance Layer
- Budget Ledger
- Enforcement Layer
- Runtime Guards
- Token semantics
- HTTP Policy
- Secret Management
- External API Adapter
- Audit/Explain
- Pattern Engine
- Review Workflow
- Operational Hardening module

## Validation

Targeted runner selftest passed in this environment:

```text
pass_script: passed
fail_script: failed as expected
timeout_script: timeout as expected
killed_process_group: true
failed: 0
```

A full CI evidence run was started; it progressed past the runner selftest and runtime
stress evidence. The complete run should be executed on the user's Windows setup as
the release gate:

```powershell
python tests\evidence_ci.py
```

## Release Gate

Stable promotion requires a complete evidence run with:

- Passed: True
- Unexpected Allows: 0
- Invariant Violations: 0
