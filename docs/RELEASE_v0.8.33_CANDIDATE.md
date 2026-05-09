# RELEASE v0.8.33_CANDIDATE

## Schwerpunkt

Phase 2: Server Mode / Integration Layer.

GateGraph erhält einen minimalen HTTP-Adapter, damit externe Systeme Governance-Entscheidungen anfragen können, ohne Governance-Logik zu duplizieren oder zu verändern.

## Änderungen

- Neu: `src/server.py`
  - `POST /evaluate`
  - `GET /status`
  - `GET /monitoring`
- Neu: `src/service_adapter.py`
  - gemeinsamer Adapterpfad für CLI und Server
  - verhindert doppelte CLI-/Server-Evaluierungslogik
- CLI refaktoriert auf `service_adapter`
- Config akzeptiert zusätzlich `mode: server`
- Neu: `tests/server_mode_evidence.py`
- Neu: `docs/SERVER_MODE.md`

## Bewusst nicht enthalten

- keine Authentifizierung
- keine TLS-/Reverse-Proxy-Konfiguration
- keine Background-Jobs
- keine Webhooks
- keine verteilte Orchestrierung
- keine Änderung an Governance Core, Rule Engine, Risk Engine oder Enforcement

## Invariante

Server Mode ist nur ein Adapter.

```text
Server → service_adapter → governance.evaluate_task
CLI    → service_adapter → governance.evaluate_task
```

## Evidence

Lokal im Linux-Arbeitscontainer ausgeführt:

```text
PASS server_mode_evidence
Summary: {'passed': 1, 'failed': 0}
```

Hinweis: Full Windows CI muss auf der Zielumgebung erneut laufen, bevor diese Candidate-Version als Stable markiert wird.
