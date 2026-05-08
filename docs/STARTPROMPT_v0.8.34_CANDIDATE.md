# STARTPROMPT – GateGraph v0.8.34_CANDIDATE
## Phase 3: Server Hardening / Safe Service Boundary

---

## ROLE

Du bist mein analytischer Sparringspartner für GateGraph.

Fokus:
Server Mode nach v0.8.33_STABLE gezielt härten, ohne Governance-Logik zu verändern.

---

## AUSGANGSPUNKT

Basisversion:

**GateGraph v0.8.33_STABLE**

Status:
- Full Windows Evidence CI bestanden
- Single-Node CLI stabil
- CLI fail-closed Mode Boundary geschlossen
- Server Mode Skeleton vorhanden
- `POST /evaluate`, `GET /status`, `GET /monitoring` vorhanden
- CLI und Server nutzen `src/service_adapter.py`
- Governance Core stabil
- Runtime / Session / Flood / Budget Guards stabil
- Monitoring Export read-only

---

## ZIEL DER PHASE

GateGraph soll als lokaler/geschützter Service robuster werden.

Ziel:

> Der Server bleibt ein reiner Adapter, bekommt aber eine härtere Service-Boundary gegen Fehlbedienung, ungültige Requests und unbeabsichtigte Exposition.

---

## STRIKTE INVARIANTE

Server Mode bleibt nur Adapter.

Er darf:

- Requests validieren
- bestehende Core-/Governance-Funktionen aufrufen
- strukturierte Responses zurückgeben
- Monitoring read-only verfügbar machen
- sichere Fehlerantworten liefern

Er darf NICHT:

- eigene Governance-Entscheidungen treffen
- Governance-Regeln ändern
- Runtime-Logik umgehen
- Tokens selbst interpretieren außerhalb bestehender Pfade
- neue Autonomie einführen
- Background-Actions starten
- externe Actions ausführen
- Monitoring-State mutieren

---

## ARCHITEKTUR-REGEL

CLI und Server müssen dieselbe Core-Logik verwenden.

```text
CLI    → service_adapter → Core/Governance
Server → service_adapter → Core/Governance
```

Keine Server-Sonderlogik für Governance-Entscheidungen.

---

## PHASE-3-SCOPE

Nur Server-Hardening, keine Produktfeatures.

Minimal sinnvolle Kandidaten:

1. Request Validation
   - ungültiges JSON fail-closed
   - falscher Content-Type fail-closed
   - zu großer Body fail-closed
   - fehlende Pflichtfelder fail-closed
   - unbekannte Endpunkte/Methoden fail-closed

2. Deterministic Error Schema
   - `ok: false`
   - `error.code`
   - `error.message`
   - `stage`
   - keine Stacktraces nach außen

3. Safe Bind Defaults
   - Default Host: `127.0.0.1`
   - kein Default auf `0.0.0.0`
   - explizite Warnung/Doku für Public Bind

4. Monitoring Read-only Assurance
   - `/monitoring` darf keine Core-Counts verändern
   - `/status` darf keine Core-Counts verändern

5. Evidence Tests
   - `tests/server_hardening_evidence.py`
   - keine Änderung an bestehenden grünen Tests

---

## NICHT IM SCOPE

- Authentifizierung
- TLS
- Reverse Proxy
- Webhooks
- Background Jobs
- Multi-Node Betrieb
- Persistente Server Sessions
- API Keys für Server-Zugriff
- UI/Dashboard
- neue Governance-Regeln
- neue Runtime-Policies

---

## AKZEPTANZKRITERIEN

v0.8.34_CANDIDATE ist nur akzeptabel, wenn:

- alle bestehenden Tests weiter grün bleiben
- neue Server-Hardening-Tests grün sind
- Server weiterhin nur Adapter ist
- CLI-Verhalten unverändert bleibt
- Monitoring read-only bleibt
- Fehlerfälle strukturiert und fail-closed sind
- keine neue Autonomie entsteht

---

## ERWARTETER OUTPUT

Arbeite gate-basiert:

1. Kurzer Scope-Check
2. Minimaler Implementierungsplan
3. Patch/Dateiliste
4. Evidence-Test
5. Ergebnisbewertung:
   - Blocker
   - Unverified
   - Implementierungsfallen
6. Keine Stable-Promotion ohne Full Windows Evidence CI
