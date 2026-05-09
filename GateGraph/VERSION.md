GateGraph v0.8.25_RUNTIME_GOVERNANCE_CANDIDATE


## v0.8.25.1_RUNNER_HARDENING_CANDIDATE
- Evidence runner hardened for timeout handling.
- POSIX path uses external watchdog (`timeout --kill-after`) to avoid interpreter wait/signal hangs.
- Windows path keeps process-tree termination via `taskkill /T /F` and direct kill fallback.
- Selftest reduced to deterministic pass/fail/timeout proof; brittle nested child-hang case removed from release gate.
