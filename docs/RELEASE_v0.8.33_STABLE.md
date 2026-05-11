# RELEASE v0.8.33_STABLE

## Schwerpunkt

Phase 2: Server Mode / Integration Layer.

GateGraph stellt einen minimalen HTTP-Adapter bereit, damit externe Systeme Governance-Entscheidungen anfragen können, ohne Governance-Logik zu duplizieren oder zu verändern.

## Änderungen gegenüber v0.8.32_STABLE

- Neu: `src/server.py`
  - `POST /evaluate`
  - `GET /status`
  - `GET /monitoring`
- Neu: `src/service_adapter.py`
  - gemeinsamer Adapterpfad für CLI und Server
  - verhindert doppelte CLI-/Server-Evaluierungslogik
- CLI refaktoriert auf `service_adapter`
- CLI Mode Boundary gehärtet:
  - CLI unterstützt ausschließlich `mode: single_node`
  - nicht unterstützte Modi schlagen fail-closed mit strukturiertem JSON-Fehler fehl
- Config akzeptiert zusätzlich `mode: server` für den Serverstart
- Neu: `tests/server_mode_evidence.py`
- Neu/aktualisiert: `docs/SERVER_MODE.md`

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

Target-environment Windows Evidence CI:

```text
CI EVIDENCE REPORT
Passed: True
```

Zusätzlich bestätigt:

```text
PASS single_node_cli_evidence
PASS server_mode_evidence
```

## Stable-Entscheidung

v0.8.33_STABLE ist nach erfolgreichem Windows-CI-Lauf und geschlossenem CLI-Fail-Closed-Blocker als **v0.8.33_STABLE** freigegeben.
