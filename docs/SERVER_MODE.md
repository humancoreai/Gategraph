# Server Mode / Integration Layer

Version: v0.8.33_STABLE

## Zweck

Server Mode stellt GateGraph als minimalen HTTP-Adapter bereit.

Er ist ausdrücklich keine neue Governance-Schicht. Externe Systeme können Entscheidungen anfragen, ohne Governance-Logik zu duplizieren oder zu umgehen.

## Invarianten

Server Mode darf:

- Requests entgegennehmen
- bestehende Core-/Governance-Pfade aufrufen
- strukturierte JSON-Responses zurückgeben
- Monitoring read-only bereitstellen

Server Mode darf nicht:

- eigene Entscheidungen treffen
- Governance-Regeln ändern
- Runtime-Logik umgehen
- Tokens außerhalb bestehender Pfade interpretieren
- neue Autonomie einführen
- Background-Actions starten

## Endpunkte

```text
POST /evaluate
GET  /status
GET  /monitoring
```

Nicht explizit erlaubte Endpunkte und Methoden werden abgelehnt.

## Start

```bash
python -m src.server --host 127.0.0.1 --port 8787
```

Optional mit Config:

```bash
python -m src.server --config config.example.yaml --host 127.0.0.1 --port 8787
```

## Beispiel: Evaluate

```bash
curl -s -X POST http://127.0.0.1:8787/evaluate \
  -H "content-type: application/json" \
  -d '{
    "task_id": "server-read-demo",
    "task_type": "agent_file_operations",
    "requested_capabilities": ["read_files"],
    "input_source": "local",
    "data_sensitivity": "internal"
  }'
```

## Architektur

CLI und Server verwenden beide `src/service_adapter.py`.

```text
CLI / Server
→ service_adapter
→ governance.evaluate_task
→ Risk Engine / Rule Engine / Event Logger / Token / Runtime Budget
```

Damit bleibt die Regel erhalten:

> Gleicher Input muss zu gleicher Governance-Entscheidung führen.

## Sicherheit

- Nur JSON-Requests mit `content-type: application/json`
- Request-Body begrenzt auf 64 KiB
- Fehlerhafte Requests liefern `ok=false`
- `GET /monitoring` ist read-only
- Server startet keine Hintergrundaktionen außer dem HTTP-Listener selbst
- Keine Authentifizierung in v0.8.33_STABLE; daher nur lokal/geschützt betreiben

## Testnachweis

```bash
python tests/server_mode_evidence.py
```

Der Evidence-Test prüft:

- `/evaluate` nutzt denselben Adapterpfad wie direkter Service-Aufruf
- `/status` liefert strukturierte Counts
- `/monitoring` liefert read-only Export
- nicht erlaubte Methoden werden abgelehnt
- malformed evaluate requests fail-closed
