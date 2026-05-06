# GateGraph Version

Current: v0.8.3-scale-safety-fix

Previous: v0.8.2-reason-normalization

Notes:
- Fixed session-budget TOCTOU risk with BEGIN IMMEDIATE transaction.
- Added projected cost reservation on session_task_links.
- Session aggregation now uses max(reserved_cost_units, actual runtime cost).
- Reason normalizer now uses explicit canonical reason keys.
- Event schema version updated to 0.8.3.
- README updated to current architecture.
