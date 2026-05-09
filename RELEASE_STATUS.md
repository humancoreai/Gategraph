# Release Status - GateGraph v0.8.15-block-c-stress-evidence

Status: Single-node PoC / stress-evidence hardening.

## Added
- `tests/block_c_stress_evidence.py` with focused Block C checks:
  - cross-task micro-flood stops at Session Budget,
  - same-agent fan-out stops at agent-level Session Budget,
  - exact budget-fill is allowed and the next action is blocked,
  - same-task repeated API-shaped loop stops at Runtime Guard before another transport call.
- `docs/BLOCK_C_STRESS_EVIDENCE.md`.

## Changed
- Evidence runner manifests include Block C stress evidence.

## Unchanged
- Enforcement remains the only authorization gatekeeper.
- Guards still only stop, never allow.
- HTTP Policy and Secret Provider order is unchanged.
- No real network client is shipped; transport remains an explicit seam.
- Production governance/enforcement/runtime semantics unchanged.

## Evidence
- Block C Stress Evidence: 4/4 passed.
- Session Budget Evidence: 6/6 passed.
- Runtime Stress Evidence: 14/14 passed.
- Runtime Guard Tests: 6/6 passed.
- External API Evidence: 7/7 passed.

## Known Limits
- Still single-node SQLite evidence.
- No distributed budget.
- No real HTTP/network failure model.
- Aggregate runner remains environment-sensitive; supervised or individual evidence paths are preferred for local proof.
