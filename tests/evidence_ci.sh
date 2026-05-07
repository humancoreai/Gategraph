#!/usr/bin/env bash
set -u
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"
mkdir -p tests/logs
RUN_ID="ci_evidence_$(date -u +%Y%m%d_%H%M%S)"
REPORT="tests/logs/${RUN_ID}.json"

names=(session_budget_evidence guard_orchestration_evidence reason_normalization_evidence scale_safety_evidence external_api_evidence runaway_cost_evidence capability_token_hardening_evidence key_rotation_evidence secret_api_integration_evidence http_policy_evidence security_finesse_evidence core_loop runtime_guard pattern_engine usage_simulation unusual_inputs agent_scenarios runtime_stress_evidence)
scripts=(tests/session_budget_evidence.py tests/guard_orchestration_evidence.py tests/reason_normalization_evidence.py tests/scale_safety_evidence.py tests/external_api_evidence.py tests/runaway_cost_evidence.py tests/capability_token_hardening_evidence.py tests/key_rotation_evidence.py tests/secret_api_integration_evidence.py tests/http_policy_evidence.py tests/security_finesse_evidence.py tests/test_loop.py tests/runtime_guard_tests.py tests/pattern_engine_tests.py tests/usage_simulation.py tests/unusual_inputs.py tests/agent_scenarios.py tests/runtime_stress_evidence.py)
started="$(date -u +%Y-%m-%dT%H:%M:%SZ)"
passed=true
commands_json=""

for i in "${!names[@]}"; do
  name="${names[$i]}"; script="${scripts[$i]}"
  rm -f gategraph.db gategraph.db-journal gategraph.db-wal gategraph.db-shm
  echo "--- $name ---"
  bash -lc "cd '$ROOT' && python -S -u tests/_run_isolated.py '$script'"
  rc=$?
  if [ "$rc" -eq 0 ]; then echo "✓ $name rc=0"; else echo "✗ $name rc=$rc"; passed=false; fi
  cmd_json="{\"name\":\"$name\",\"returncode\":$rc}"
  if [ -z "$commands_json" ]; then commands_json="$cmd_json"; else commands_json="$commands_json,$cmd_json"; fi
done

finished="$(date -u +%Y-%m-%dT%H:%M:%SZ)"
cat > "$REPORT" <<JSON
{"run_id":"$RUN_ID","started_at":"$started","finished_at":"$finished","passed":$passed,"commands":[$commands_json],"notes":["Minimal aggregate runner with one fresh shell per evidence group; avoids output-capture interactions."]}
JSON

echo
echo "CI EVIDENCE REPORT"
echo "Log: $REPORT"
echo "Passed: $passed"
[ "$passed" = true ]
