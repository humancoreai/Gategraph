# Operator Workflows / Playbooks (v0.8.42)

## Zweck

Der Operator Workflow Layer ergänzt GateGraph um statische Playbooks und eine dokumentierende Workflow-Sicht.

Er verbindet erkannte Muster, Reason Codes, Guards und Incidents mit neutralen Arbeitslabels für menschliche Operatoren.

## Invarianten

- Keine Änderung an Governance, Enforcement, Runtime, Budget oder Audit.
- Keine automatische Reaktion.
- Keine Policy- oder Rule-Updates.
- Keine Root-Cause-Aussage.
- Keine Priorisierung, kein Ranking, kein Scoring.
- Keine Empfehlungssprache.

## Komponenten

### `playbooks/*.json`

Statische, versionierbare Playbook-Dateien.

Pflichtfelder:

- `playbook_id`
- `version`
- `trigger.reason_codes`
- `trigger.guards`
- `steps`
- `notes`

Die Reihenfolge der `steps` ist eine gespeicherte Listenform, keine Prioritäts- oder Ablaufentscheidung.

### `src/operator_workflow.py`

Enthält:

- `load_playbooks`
- `match_playbooks`
- `append_workflow_event`
- `read_workflow_events`
- `link_incident_playbooks`
- `workflow_snapshot`
- `assert_no_workflow_interpretation_labels`

## Workflow Log

Workflow-Einträge werden als JSONL-Dokumentation geschrieben.

Standardpfad:

```text
operator_logs/workflow_events.jsonl
```

Die Einträge enthalten nur:

- Playbook-Referenz
- Task-/Filterbezug
- dokumentierte Schrittlabels
- Zeitstempel
- optionalen Operator-Kommentar

Sie haben keine Wirkung auf Systementscheidungen.

## Evidence

Nachweis über:

```text
tests/operator_workflow_evidence.py
```

Abgedeckt:

- Playbooks laden
- deskriptives Matching
- append-only Workflow-Dokumentation
- Incident-Referenzierung
- reproduzierbarer Snapshot
- keine Governance-Entscheidungsänderung
- Sprach-/Label-Check gegen versteckte Bewertung
