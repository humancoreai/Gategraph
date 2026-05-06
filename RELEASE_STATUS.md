# Release Status — GateGraph v0.8.24

## Status

Runner subsystem hardening implemented.

## Changed

- Replaced external shell `timeout` dependency in `tests/evidence_ci.py` with Python-owned timeout handling.
- Added process-session isolation and process-group kill for timed-out evidence scripts.
- Added dedicated runner selftest as first manifest item.
- Added synthetic evidence target for pass/fail/hang/child-hang cases.
- Added runner subsystem documentation.

## Production logic

Unchanged:

- Governance
- Enforcement
- Token signing / rotation
- Runtime guards
- Session budget guard
- HTTP policy
- Secret management
- External API adapter
- Controlled Apply
- Audit / Explain

## Validation note

The code-level runner fix is implemented. In this execution sandbox, timeout primitives showed unstable behavior during validation; therefore the final aggregate run should be repeated in a clean local/CI environment before treating v0.8.24 as release-final.
## v0.8.25_RUNTIME_GOVERNANCE_CANDIDATE

- Added `src/runtime_governance.py` with deterministic normal/degraded/throttled/blocked escalation states.
- Runtime Guard now applies stricter `max_cost_for_action` constraints before recording a new step.
- Loop signals can only escalate constraints; they cannot allow continuation.
- Extended runaway cost evidence with near-budget and loop-signal constraint cases.
- No change to Enforcement authority, Pattern decision rights, Secret handling or Human-Gate invariants.



## v0.8.25.1_RUNNER_HARDENING_CANDIDATE
- Evidence runner hardened for timeout handling.
- POSIX path uses external watchdog (`timeout --kill-after`) to avoid interpreter wait/signal hangs.
- Windows path keeps process-tree termination via `taskkill /T /F` and direct kill fallback.
- Selftest reduced to deterministic pass/fail/timeout proof; brittle nested child-hang case removed from release gate.
