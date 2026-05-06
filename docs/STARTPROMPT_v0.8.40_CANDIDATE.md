# STARTPROMPT – GateGraph v0.8.40_CANDIDATE

## Phase 8: Operator Control / Debug Interface

### ROLE

Du bist mein analytischer Sparringspartner für GateGraph.

Fokus:
Eine kontrollierte Operator-/Debug-Schicht auf Basis der Observability-Daten bauen – ohne Änderung der Governance-, Runtime- oder Entscheidungslogik.

---

## AUSGANGSPUNKT

Basisversion:

**GateGraph v0.8.39_STABLE**

Status:

- Runtime Cost Governance aktiv
- Loop Detection aktiv
- Decision Trace Reconstruction vorhanden
- Guard Attribution eindeutig
- Explain Snapshot vorhanden
- Cost Timeline vorhanden
- Aggregated Observability im Monitoring vorhanden
- Full Evidence CI grundsätzlich vorgesehen; Observability Evidence grün
- Fail-Closed System konsistent

---

## ZIEL DER PHASE

GateGraph soll für einen Operator gezielt überprüfbar werden:

> Nicht nur „was ist passiert?“, sondern „welche Debug-Information darf ein Operator sicher abrufen?“

Ziel ist eine **read-only Debug Interface Boundary**.

---

## STRIKTE INVARIANTE

Der Operator-/Debug-Layer darf:

- vorhandene Traces anzeigen
- Explain Snapshots abrufen
- Cost Timeline abrufen
- Monitoring-Zusammenfassungen lesen
- Task-Status rekonstruieren

Der Operator-/Debug-Layer darf NICHT:

- Entscheidungen beeinflussen
- Guards neu ausführen
- Budgets verändern
- Tokens erzeugen oder widerrufen
- Core-Daten mutieren
- automatische Reparaturen durchführen
- neue Autonomie einführen

---

## PHASE-8-SCOPE

### 1. Debug Read Model

Ziel:
Ein klar getrenntes Read Model für Operator-Abfragen.

Muss enthalten:

- `task_id`
- final decision
- triggering guard
- normalized reason
- runtime steps count
- cost usage
- trace availability

### 2. Operator Debug Functions

Minimalfunktionen:

- `get_task_debug(task_id)`
- `get_task_explain(task_id)`
- `get_task_cost_timeline(task_id)`
- `get_operator_summary()`

Alle Funktionen read-only.

### 3. Debug Boundary Tests

Nachweis:

- Debug liest nur bestehende Daten
- keine Anzahl von Steps/Decisions/Budgets verändert sich
- fehlende Task liefert fail-closed/empty-safe Ergebnis
- keine Guard-Neuausführung

### 4. Optional Server Exposure Check

Nur prüfen, nicht automatisch erweitern:

- Soll Debug über Server-Endpunkt sichtbar werden?
- Wenn ja: eigener klarer read-only Endpunkt
- Keine Änderung an `/evaluate`

---

## NICHT IM SCOPE

- UI
- Visualisierung
- Mutating Admin Actions
- Retry/Repair
- Budget Reset
- Token Revocation
- Multi-Node Operator Console
- Auth-System für Operatoren

---

## AKZEPTANZKRITERIEN

v0.8.40_CANDIDATE nur gültig wenn:

- alle bestehenden Tests grün bleiben
- `operator_debug_evidence` grün ist
- Debug-Layer keine Core-Daten verändert
- kein Guard durch Debug erneut entscheidet
- fehlende Task deterministisch und sicher behandelt wird
- `/evaluate` unverändert bleibt

---

## ERWARTETER OUTPUT

- Scope-Check
- Implementierungsplan
- Patch-/Dateiliste
- Evidence-Test
- Bewertung:
  - Blocker
  - Unverified
  - Implementierungsfallen

---

## HINWEIS

Diese Phase ist keine Admin-Konsole.

Sie ist die sichere Leseschicht zwischen:

- Systemlogik
- Observability
- menschlicher Bedienbarkeit

Kurz gesagt:

> v0.8.39 erklärt Entscheidungen.  
> v0.8.40 macht diese Erklärung kontrolliert abrufbar.
