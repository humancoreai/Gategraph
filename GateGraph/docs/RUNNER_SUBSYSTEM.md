# Runner Subsystem v0.8.24

## Scope

The evidence runner is an isolated test/evidence subsystem. It must not alter production governance, enforcement, token, runtime, HTTP-policy, secret, external API or controlled-apply semantics.

## Root cause addressed

The previous aggregate runner relied on an external `timeout` wrapper. That made the parent process dependent on shell-level timeout behavior and did not provide a Python-owned upper bound around the wait path.

## Design

- file-backed stdout/stderr to avoid pipe drain deadlocks
- `subprocess.Popen(..., start_new_session=True)` on POSIX
- Python-level `proc.wait(timeout=...)`
- on timeout: `os.killpg(proc.pid, SIGKILL)`
- bounded reap after kill
- fail-closed timeout semantics: timeout is a failed evidence command, even if a script printed a passing summary before hanging
- DB reset verification warnings are recorded per command
- `evidence_runner_selftest` is first in the manifest

## Selftest coverage

`tests/evidence_runner_selftest.py` verifies:

1. passing script returns passed
2. failing script returns failed
3. hung script times out
4. spawned child process is killed with the process group

## Non-goals

- no production behavior changes
- no relaxation of evidence failures
- no acceptance of summary-before-timeout as pass
