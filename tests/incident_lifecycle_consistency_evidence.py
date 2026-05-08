from __future__ import annotations

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from dataclasses import asdict
from src import incident_state_manager, operational_hardening


def make_incident(state: str = "open") -> operational_hardening.IncidentRecord:
    return operational_hardening.IncidentRecord(
        incident_id="inc-sem-001",
        severity="high",
        trigger_type="semantic_registry",
        trigger_ref="INV-INC-001",
        state=state,
        reason_code="INCIDENT_LIFECYCLE_EVIDENCE",
        details={},
        created_at="2026-05-08T00:00:00+00:00",
    )


def check(name: str, ok: bool, detail: dict) -> tuple[str, bool, dict]:
    print(("✓" if ok else "✗") + f" {name}: {detail}")
    return name, ok, detail


def blocks(fn) -> bool:
    try:
        fn()
    except ValueError:
        return True
    return False


def main() -> int:
    checks = []
    inc = make_incident()
    ack = incident_state_manager.transition_incident_state(inc, "acknowledged", now="2026-05-08T00:01:00+00:00")
    res = incident_state_manager.transition_incident_state(ack, "resolved", now="2026-05-08T00:02:00+00:00")
    archived = incident_state_manager.transition_incident_state(res, "archived", now="2026-05-08T00:03:00+00:00")

    checks.append(check("forward_lifecycle_supported", archived.state == "archived", {"states": [inc.state, ack.state, res.state, archived.state]}))
    checks.append(check("direct_skip_blocked", blocks(lambda: incident_state_manager.transition_incident_state(inc, "resolved")), {}))
    checks.append(check("regression_blocked", blocks(lambda: incident_state_manager.transition_incident_state(res, "acknowledged")), {}))
    checks.append(check("archive_reopen_blocked", blocks(lambda: incident_state_manager.transition_incident_state(archived, "open")), asdict(archived)))

    valid_history = incident_state_manager.validate_incident_transition_history(["open", "acknowledged", "resolved", "archived"])
    invalid_history = incident_state_manager.validate_incident_transition_history(["open", "acknowledged", "resolved", "open"])
    checks.append(check("append_only_history_valid", bool(valid_history["ok"]), valid_history))
    checks.append(check("append_only_history_regression_detected", not bool(invalid_history["ok"]), invalid_history))

    failed = [name for name, ok, _ in checks if not ok]
    print("Summary:", {"passed": len(checks) - len(failed), "failed": len(failed), "failed_checks": failed})
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
