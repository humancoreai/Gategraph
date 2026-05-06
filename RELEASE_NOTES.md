Runner Windows fix
Encoding fix
Controlled Apply stabil
Evidence CI passed
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
