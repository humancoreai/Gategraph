# Release Notes – v0.8.35_CANDIDATE

## Phase

Phase 4: Deterministic API Surface / Contract Stabilization

## Scope

- Neues `src/response_normalizer.py` als rein struktureller Server-Layer.
- Server-Responses auf festes Schema normalisiert: `ok`, `data`, `error`, `meta`.
- Fehlercodes auf stabile, maschinenlesbare Codes begrenzt.
- Request-Metadaten ergänzt: `schema_version`, `request_id`, `timestamp`, `stage`.
- `POST /evaluate` gibt keine ungefilterten Core-Top-Level-Outputs mehr zurück.
- `GET /status` und `GET /monitoring` werden ebenfalls in das Schema eingebettet.
- Neue Evidence: `tests/api_contract_evidence.py`.

## Invarianten

- Server bleibt Adapter.
- CLI bleibt unverändert.
- Governance-Core wird nicht verändert.
- Keine zusätzliche Intelligenz, keine Umdeutung von Entscheidungen.
- Keine State-Mutation durch Response-Normalisierung.

## Evidence

Gezielt geprüft:

- `api_contract_evidence`: PASS
- `server_mode_evidence`: PASS
- `server_hardening_evidence`: PASS

Hinweis: Der vollständige Aggregate-Run wurde in dieser Containerumgebung nicht vollständig beendet; bekannte Umgebungseigenheit beim Evidence-Runner/Interpreter. Die Phase-4-relevanten Evidence-Tests wurden separat erfolgreich ausgeführt.
