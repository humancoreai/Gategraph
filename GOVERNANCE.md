# GOVERNANCE.md

## Zweck

Dieses Dokument beschreibt die Governance-Prinzipien hinter GateGraph.
Es erklärt **warum** das System so gebaut ist, wie es gebaut ist.

GateGraph ist kein Feature-System, sondern ein **Kontroll- und Durchsetzungssystem** für AI-gestützte Ausführung.

---

## Grundprinzip

> **Das Regelwerk ist der Architekt.
> Code ist die Ausführung.**

Alle zentralen Designentscheidungen folgen festen Regeln, nicht situativen Einzelentscheidungen.

---

## Rollenmodell (Chefetagen-Modell)

* **Mensch**

  * Strategische Entscheidungshoheit
  * Definiert Scope und Prioritäten

* **Governance (dieses Regelwerk + Review)**

  * Sicherstellung von Konsistenz, Sicherheit und Struktur
  * Drift-Kontrolle

* **Implementierung (Agenten / Modelle)**

  * Reine Ausführung
  * Keine Scope- oder Architekturentscheidungen

---

## Entwicklungsprozess (Gate-System)

Jede Entwicklung folgt strikt diesem Ablauf:

1. Scope definieren (SSOT)
2. Implementierung delegieren
3. Strikter Review (Architektur, Security, Drift)
4. Governance-Fix (falls notwendig)
5. Technische Konsolidierung
6. Snapshot (Versionierung)
7. Erst dann nächstes Gate

**Prinzip:**

> Stabilisieren vor Erweitern

---

## Zentrale Invarianten

Diese Regeln gelten systemweit und sind nicht optional:

* Fail-closed statt fail-open
* Keine impliziten Aktionen
* Strikte Trennung:

  * Lesen vs. Handeln
* Deterministisches Verhalten bevorzugt
* Reversibilität sicherstellen
* Keine versteckten Side Effects

---

## Security-Grundsätze

* Keine hardcodierten Secrets oder Tokens
* Least-Privilege-Prinzip
* Untrusted Input wird immer als potenziell feindlich behandelt
* Schutz vor:

  * Prompt Injection
  * Datenvergiftung
* Klare Kontrollpunkte vor Ausführung (Gates)

---

## Architekturprinzipien

* Struktur > Features
* Dokumentation ist Teil des Systems (SSOT)
* Keine implizite Logik
* Explizite Zustände und Übergänge
* Keine „magischen“ Automatismen

---

## Enforcement vs. Proposal

GateGraph unterscheidet zwei Klassen von Regeln:

### Enforcement (harte Regeln)

* Werden technisch erzwungen
* Verletzungen führen zu:

  * Abbruch
  * Blockierung
* Beispiele:

  * Cost Limits
  * Iteration Caps
  * Policy Checks

### Proposal (Best Practices)

* Werden vorgeschlagen, nicht erzwungen
* Dienen der Strukturverbesserung
* Beispiele:

  * Pattern-Optimierungen
  * Refactoring-Hinweise

---

## Runtime Governance (GateGraph)

GateGraph implementiert Teile dieses Regelwerks als Laufzeitsystem:

* Loop Detection (z. B. Agent-Ping-Pong)
* Cost Control / Budget Limits
* Action-Signature Tracking
* Entscheidungs-Gates (continue / stop)

Erweitert in aktuellen Versionen:

* **Budget Ledger (systemweit, hierarchische Scopes)**
* **Cross-Session Budget Enforcement**
* **Reservation → Consume → Release**
* **Deterministische Escalation States (normal, degraded, throttled, blocked)**

Ziel:

> **Kontrollierbare, begrenzte und überprüfbare Ausführung**

---

## Operational Governance

Neben der Entscheidungslogik enthält GateGraph Mechanismen zur Überprüfung des Systemzustands:

* Budget Snapshots (systemweit und pro Scope)
* Audit Replay zur Konsistenzprüfung
* Erkennung von Budget Drift und Inkonsistenzen
* Append-only Incident Records

Ziel:

> **Nicht nur korrekt entscheiden, sondern Korrektheit überprüfbar machen**

---

## Audit & Explain

GateGraph behandelt Audit nicht als Logging, sondern als Beweisschicht:

* Alle Entscheidungen sind rekonstruierbar
* Reason Codes sind stabil und normalisiert
* Entscheidungen sind deterministisch ableitbar

Prinzip:

> **Jede Entscheidung muss erklärbar und überprüfbar sein**

---

## Halluzinationscheck (implizites Konzept)

Jede Bewertung, Entscheidung oder Ausgabe muss intern geprüft werden auf:

* Konsistenz mit bekannten Regeln
* Fehlen unbelegter Annahmen
* Nachvollziehbarkeit

Hinweis:
Dieses Konzept ist aktuell prozessual umgesetzt, nicht vollständig im System formalisiert.

---

## Dokumentationsprinzip

Ein Repository ist nur vollständig, wenn folgende Dokumente vorhanden sind:

* README.md
* ARCHITECTURE.md
* SECURITY.md
* GOVERNANCE.md (dieses Dokument)

**Prinzip:**

> Dokumentation ist kein Zusatz, sondern Teil des Systems.

---

## Bewusste Trade-offs

Dieses System priorisiert:

* Sicherheit
* Kontrolle
* Reproduzierbarkeit

auf Kosten von:

* Geschwindigkeit
* initialem Entwicklungsaufwand

Diese Entscheidung ist bewusst getroffen.

---

## Abgrenzung

GateGraph ist **kein**:

* autonomes Entscheidungssystem
* vollständiger Policy-Interpreter
* Ersatz für menschliche Governance

Die finale Kontrolle liegt immer beim Menschen.

---

## Status

Dieses Dokument beschreibt den aktuellen Stand der Governance.
Es ist bewusst:

* menschenlesbar
* flexibel anpassbar
* nicht vollständig in Code überführt

---

## Leitsatz

> **Struktur schlägt Modell.
> Kontrolle schlägt Geschwindigkeit.
> Explizit schlägt implizit.
> Nachvollziehbarkeit schlägt Komfort.**
