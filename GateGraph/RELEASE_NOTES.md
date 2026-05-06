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

