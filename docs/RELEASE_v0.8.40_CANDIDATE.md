# RELEASE v0.8.40_STABLE

## Phase

Operator Control / Debug Interface

## Base

v0.8.39_STABLE

## Ziel

Operative Nutzbarkeit der vorhandenen Observability-Daten herstellen, ohne Systemlogik zu verändern.

## Änderungen

- Neuer read-only Operator Layer: `src/operator_control.py`
- Neue Evidence: `tests/operator_evidence.py`
- Evidence CI Manifest um `operator_evidence` erweitert
- Dokumentation: `docs/OPERATOR_CONTROL.md`
- Version auf `v0.8.40_STABLE` gesetzt

## Invarianten

- Keine Änderung der Governance Core Logic
- Keine Änderung der Guards
- Keine Mutation von Runtime-Daten
- Keine neue Entscheidungslogik
- Operator-Funktionen sind read-only

## Stable-Bedingung

- `python tests/operator_evidence.py` grün
- `python tests/evidence_ci.py` grün
- Keine Repo-Hygiene-Funde vor Promotion
