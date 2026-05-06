# Runner POSIX Hardening

Version: v0.8.27.1_RUNNER_POSIX_HARDENING_CANDIDATE

## Scope

This patch hardens only the evidence runner. It does not change production governance,
enforcement, budget, runtime, token, HTTP, secret, audit, explain, pattern or review logic.

## Change

The POSIX evidence path no longer wraps evidence scripts with the external `timeout`
binary. It now uses the same Python-owned supervision model as the Windows path:

- `subprocess.Popen(...)`
- `start_new_session=True` on POSIX
- `proc.wait(timeout=...)`
- hard process-group kill on timeout
- file-backed stdout/stderr remains unchanged

## Reason

The external `timeout` wrapper can leave the Python runner waiting on process-exit
semantics outside its own control. The runner must own timeout decisions directly and
report timeout fail-closed.

## Invariants

- Evidence timeout remains fail-closed.
- Production code is untouched.
- Guards and governance semantics are unchanged.
- Timeout result is reported as `status=timeout`, `returncode=124`.
- Process-tree kill remains best-effort and recorded in evidence output.

## Known boundary

A true POSIX kernel D-state process cannot be forcibly resolved from normal user-space.
This patch prevents the evidence runner from relying on shell timeout wrappers; CI-level
outer timeouts remain the correct last-resort guard.
