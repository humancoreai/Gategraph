# Release Candidate – v0.8.27 Operational Hardening

## Status

Candidate, nicht Stable.

## Ziel

Erste Operational-Hardening-Schicht ohne Autonomie-Erweiterung:

- Budget Ledger sichtbar machen
- Audit-Konsistenz deterministisch prüfen
- Incident-Zustände append-only dokumentieren

## Neue Dateien

- `src/operational_hardening.py`
- `tests/operational_hardening_evidence.py`
- `docs/OPERATIONAL_HARDENING.md`

## Evidence

Targeted Evidence:

```text
/usr/bin/python3 tests/operational_hardening_evidence.py
```

Ergebnis:

```text
Summary: {'passed': 6, 'failed': 0, 'unexpected_allows': 0, 'invariant_violations': 0}
```

## Einschränkung

Der vollständige Evidence-CI-Run wurde in dieser Containerumgebung nicht abgeschlossen, weil der vorhandene Evidence-Runner/Selftest-Prozess hier hängen bleibt. Der neue Targeted Evidence Test läuft durch. Auf Windows sollte der bestehende `python tests\evidence_ci.py` erneut als Release-Gate laufen.

## Invariantenprüfung

- keine Aktionserlaubnis durch Operational Hardening
- keine Änderung an Enforcement, Governance-Entscheidungslogik oder Token-Ausstellung
- keine automatische Recovery
- Incident Detection ist Beobachtung/Dokumentation, nicht Handlung
