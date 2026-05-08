# Block C Stress Evidence

Version: v0.8.15-block-c-stress-evidence

## Scope

Block C validates stress/runaway behavior without adding new production features.

Covered scenarios:

1. **Micro-flood across tasks**
   - Many individually cheap API-shaped actions share one session budget.
   - Expected: first actions complete, later actions stop at `session_budget` before transport.

2. **Same-agent fan-out**
   - Multiple tasks by the same actor share an agent-level budget.
   - Expected: second task stops at `session_budget` due `max_agent_cost_units`.

3. **Budget boundary**
   - One action exactly fills remaining session budget.
   - Expected: exact-fill action is allowed; next action is blocked.

4. **Same-task repeated API loop**
   - Same token/task repeatedly targets the same API-shaped action.
   - Expected: Runtime Guard stops the third action via `repeated_action_limit` before another transport call.

## Invariants checked

- Session Budget stops cross-task micro-floods.
- Agent-level budget stops same-agent task fan-out.
- Runtime Guard stops repeated-action loops inside one task.
- Transport is not reached after a stop decision.
- Existing production core semantics remain unchanged.

## Known Limit

This is still single-node SQLite evidence. It does not prove distributed-budget behavior, real network failure behavior, or production telemetry/alerting.
