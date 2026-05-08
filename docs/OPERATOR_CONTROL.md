# GateGraph v0.8.40 — Operator Control / Debug Interface

## Zweck

Der Operator Layer macht vorhandene Observability-Daten operativ nutzbar, ohne Systemverhalten zu beeinflussen.

## Strikte Invariante

Der Operator Layer ist passiv und read-only.

Er darf:
- Decisions lesen
- Traces rekonstruieren
- vorhandene Snapshots anzeigen
- nach exakten Kriterien filtern
- Aggregationen zu konkreten Fällen zurückführen

Er darf nicht:
- Core-Daten verändern
- Entscheidungen beeinflussen
- neue Governance-Logik einführen
- Policy-Tuning oder Reparaturen durchführen
- Interpretationen oder Gewichtungen hinzufügen

## Enthaltene Funktionen

- `inspect_decision(conn, task_id)`
- `explain_compact(conn, task_id)`
- `query_traces(conn, TraceQuery(...))`
- `drilldown_stop_reason(conn, reason_code)`
- `incident_related_decisions(incident)`
- `alert_root_cause_trace(conn, alert)`

## CLI

```bash
python -m src.operator_control --db gategraph.db inspect <task_id>
python -m src.operator_control --db gategraph.db explain <task_id>
python -m src.operator_control --db gategraph.db query --decision stop --guard runtime_cost_guard
python -m src.operator_control --db gategraph.db drilldown-stop-reason <REASON_CODE>
```

## Evidence

```bash
python tests/operator_evidence.py
python tests/evidence_ci.py
```

## Nicht im Scope

- UI / Dashboard
- Visualisierung
- automatische Reparaturen
- Multi-Node Debugging
- Performance-Optimierung
