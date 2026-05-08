# Operational Hardening – v0.8.27.1 Stable

## Scope

Operational Hardening macht den vorhandenen Governance-Zustand sichtbar und prüfbar, ohne neue Autonomie einzuführen.

## Enthalten

- Budget Snapshot über alle Budget-Scopes
- deterministischer Audit-Replay-Konsistenzcheck
- Incident-Erkennung für Budget- und Audit-Anomalien
- append-only Incident Records

## Nicht enthalten

- keine UI
- kein externes Monitoring
- kein automatisches Recovery
- keine Pattern-Engine-Erweiterung
- keine externe API-Integration

## Invarianten

- Operational Hardening darf keine Aktionen erlauben
- Replay repariert nichts automatisch
- Incident Detection blockiert nicht selbst, sondern dokumentiert fail-closed Zustände
- Recovery bleibt Governance-Aufgabe
- Budget Authority bleibt unverändert bei Governance

## Evidence

Neues Evidence-Skript:

```text
tests/operational_hardening_evidence.py
```

Es prüft:

- Snapshot erzeugt Actor-Budget-Sicht
- sauberer Zustand bleibt anomalfrei
- Audit-Replay ist bei konsistentem Zustand ok
- künstlicher Budget-Drift wird erkannt
- Replay fällt bei Drift fail-closed
- Incident Records werden append-only erzeugt
