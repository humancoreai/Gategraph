#!/usr/bin/env bash
set -u
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"
mkdir -p tests/logs
RUN_ID="ci_evidence_$(date -u +%Y%m%d_%H%M%S)"
REPORT="tests/logs/${RUN_ID}.json"
TMPDIR="$(mktemp -d)"
trap 'rm -rf "$TMPDIR"' EXIT

names=(runtime_stress_evidence session_budget_evidence guard_orchestration_evidence reason_normalization_evidence scale_safety_evidence external_api_evidence runaway_cost_evidence capability_token_hardening_evidence key_rotation_evidence secret_api_integration_evidence core_loop runtime_guard pattern_engine usage_simulation unusual_inputs agent_scenarios)
scripts=(tests/runtime_stress_evidence.py tests/session_budget_evidence.py tests/guard_orchestration_evidence.py tests/reason_normalization_evidence.py tests/scale_safety_evidence.py tests/external_api_evidence.py tests/runaway_cost_evidence.py tests/capability_token_hardening_evidence.py tests/key_rotation_evidence.py tests/secret_api_integration_evidence.py tests/test_loop.py tests/runtime_guard_tests.py tests/pattern_engine_tests.py tests/usage_simulation.py tests/unusual_inputs.py tests/agent_scenarios.py)
started="$(date -u +%Y-%m-%dT%H:%M:%SZ)"
passed=true
commands_json=""

b64_tail() { tail -c 4000 "$1" | base64 | tr -d '\n'; }

for i in "${!names[@]}"; do
  name="${names[$i]}"; script="${scripts[$i]}"
  out="$TMPDIR/${name}.out"; err="$TMPDIR/${name}.err"
  rm -f gategraph.db gategraph.db-journal gategraph.db-wal gategraph.db-shm
  timeout 60 python -S -u tests/_run_isolated.py "$script" >"$out" 2>"$err"
  rc=$?
  if [ "$rc" -eq 0 ]; then echo "✓ $name rc=0"; else echo "✗ $name rc=$rc"; passed=false; fi
  stdout_tail_b64="$(b64_tail "$out")"
  stderr_tail_b64="$(b64_tail "$err")"
  cmd_json="{\"name\":\"$name\",\"command\":[\"timeout\",\"60\",\"python\",\"-S\",\"-u\",\"$script\"],\"returncode\":$rc,\"stdout_tail_b64\":\"$stdout_tail_b64\",\"stderr_tail_b64\":\"$stderr_tail_b64\"}"
  if [ -z "$commands_json" ]; then commands_json="$cmd_json"; else commands_json="$commands_json,$cmd_json"; fi
done

finished="$(date -u +%Y-%m-%dT%H:%M:%SZ)"
cat > "$REPORT" <<JSON
{
  "run_id": "$RUN_ID",
  "started_at": "$started",
  "finished_at": "$finished",
  "passed": $passed,
  "commands": [$commands_json],
  "notes": ["Shell runner isolates each evidence script in a hard-timeboxed process; output tails are base64 encoded to avoid Python shutdown/import side effects in the runner itself."]
}
JSON

echo
echo "CI EVIDENCE REPORT"
echo "Log: $REPORT"
echo "Passed: $passed"
[ "$passed" = true ]
