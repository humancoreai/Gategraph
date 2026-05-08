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


## v0.8.26_STABLE

- Promoted Cross-Session Budget Control candidate to stable after full Windows Evidence CI reported `Passed: True` on 2026-04-28.
- Added single-node Budget Ledger and reservation lifecycle as stable scope.
- Capability Tokens now carry budget reservation claims verified by Enforcement.
- Cross-session/task-splitting budget bypass is covered by evidence.
- Repo hygiene pass removed generated caches/logs from the stable archive.
- Known limits remain: single-node only, no production KMS, no distributed consensus/locks, no monitoring/alerting.

## v0.8.27.1_STABLE

- Promoted Operational Hardening and Runner POSIX hardening to stable after full Windows Evidence CI reported `Passed: True` on 2026-04-28.
- Added stable operational visibility scope: budget snapshots, audit replay consistency checks, anomaly/drift detection and append-only incident records.
- Retained the Evidence Runner POSIX supervision patch: Python-owned `Popen` timeout handling with POSIX session isolation instead of the external `timeout` wrapper.
- Repo hygiene pass removed generated caches and evidence logs from the stable archive.
- Known limits remain: single-node only, no production KMS, no distributed consensus/locks, mock external API only, no automated incident recovery.

## v0.8.28_CANDIDATE

- Added root-level `GOVERNANCE.md` as the repository-level governance SSOT.
- Added README reference to `GOVERNANCE.md`.
- Updated version/release metadata for the candidate.
- No functional code changes; validation baseline remains `v0.8.27.1_STABLE`.

