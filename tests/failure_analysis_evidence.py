import json
import sys
from pathlib import Path
from datetime import datetime, timezone

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.failure_analysis import (
    assert_no_interpretation_labels,
    compare_decisions,
    compare_guards,
    failure_clusters,
    pattern_detection,
    postmortem_view,
    timeline_correlation,
)


def fixture_events():
    return [
        {
            "task_id": "T-1",
            "decision": "continue",
            "guard": "runtime_guard",
            "normalized_reason": {"code": "OK_ACTION_READY"},
            "timestamp": "2026-05-06T10:00:00+00:00",
            "cost_units": 1,
            "runtime_seconds": 0.1,
        },
        {
            "task_id": "T-1",
            "decision": "stop",
            "guard": "runtime_cost_guard",
            "normalized_reason": {"code": "RT_PROJECTED_COST_LIMIT"},
            "timestamp": "2026-05-06T10:05:00+00:00",
            "cost_units": 6,
            "runtime_seconds": 0.2,
        },
        {
            "task_id": "T-2",
            "decision": "stop",
            "guard": "runtime_guard",
            "normalized_reason": {"code": "RT_LOOP_DETECTED"},
            "timestamp": "2026-05-06T11:00:00+00:00",
            "cost_units": 2,
            "runtime_seconds": 0.4,
        },
        {
            "task_id": "T-3",
            "decision": "stop",
            "guard": "runtime_cost_guard",
            "normalized_reason": {"code": "RT_PROJECTED_COST_LIMIT"},
            "timestamp": "2026-05-06T11:30:00+00:00",
            "cost_units": 7,
            "runtime_seconds": 0.3,
        },
    ]


def check(name, condition, details):
    if not condition:
        raise AssertionError(f"{name} failed: {details}")
    print(f"✓ {name}: {details}")


def main():
    events = fixture_events()
    results = {}

    patterns = pattern_detection(events)
    results["pattern_detection"] = patterns
    check(
        "pattern_detection_counts_reason_codes",
        patterns["reason_code_counts"] == {
            "OK_ACTION_READY": 1,
            "RT_LOOP_DETECTED": 1,
            "RT_PROJECTED_COST_LIMIT": 2,
        },
        patterns["reason_code_counts"],
    )

    check(
        "pattern_detection_counts_guards",
        patterns["guard_counts"] == {"runtime_cost_guard": 2, "runtime_guard": 2},
        patterns["guard_counts"],
    )

    decision_compare = compare_decisions(events)
    results["compare_decisions"] = decision_compare
    check(
        "compare_decisions_stop_continue",
        decision_compare["decision_groups"]["continue"]["case_count"] == 1
        and decision_compare["decision_groups"]["stop"]["case_count"] == 3,
        decision_compare["decision_groups"],
    )

    guard_compare = compare_guards(events)
    results["compare_guards"] = guard_compare
    check(
        "compare_guards_descriptive",
        guard_compare["guard_groups"]["runtime_cost_guard"]["case_count"] == 2,
        guard_compare["guard_groups"],
    )

    clusters = failure_clusters(events)
    results["failure_clusters"] = clusters
    check(
        "failure_clusters_grouping_only",
        len(clusters["clusters"]) == 3
        and clusters["analysis_mode"] == "descriptive_grouping_only",
        clusters,
    )

    postmortem = postmortem_view(events, guard="runtime_cost_guard")
    results["postmortem_view"] = postmortem
    check(
        "postmortem_filter_runtime_cost_guard",
        postmortem["case_count"] == 2
        and postmortem["reason_code_counts"] == {"RT_PROJECTED_COST_LIMIT": 2},
        postmortem,
    )

    timeline = timeline_correlation(events)
    results["timeline_correlation"] = timeline
    check(
        "timeline_correlation_descriptive_buckets",
        timeline["time_buckets"]["2026-05-06T10Z"]["case_count"] == 2
        and timeline["time_buckets"]["2026-05-06T11Z"]["case_count"] == 2,
        timeline["time_buckets"],
    )

    check(
        "no_interpretation_labels",
        assert_no_interpretation_labels(results),
        results,
    )

    check(
        "interpretation_label_checker_allows_stop",
        assert_no_interpretation_labels({"stop": {"case_count": 1}}),
        {"stop": {"case_count": 1}},
    )

    check(
        "read_only_input_not_mutated",
        events == fixture_events(),
        events,
    )

    report = {
        "schema_version": "0.8.41",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "summary": {"passed": 9, "failed": 0},
        "results": results,
    }

    print("\nFAILURE ANALYSIS EVIDENCE REPORT")
    print(json.dumps(report["summary"], indent=2, sort_keys=True))
    print("PASS failure_analysis_evidence")


if __name__ == "__main__":
    main()
