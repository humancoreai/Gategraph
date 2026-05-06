# API Contract v0.8.35

## Zweck

Phase 4 stabilisiert die Server-Antworten als externe Vertragsfläche.
Der Server bleibt Adapter und normalisiert nur die Response-Struktur.

## Top-Level-Schema

Jede Server-Response nutzt exakt diese Top-Level-Felder:

```json
{
  "ok": true,
  "data": {},
  "error": null,
  "meta": {
    "schema_version": "0.8.35",
    "request_id": "uuid",
    "timestamp": "utc-iso8601",
    "stage": "server|core|request_validation|routing"
  }
}
```

Regeln:

- `ok=true` bedeutet: `data` ist ein Objekt, `error=null`.
- `ok=false` bedeutet: `data=null`, `error` ist ein Objekt.
- Es gibt keine zusätzlichen Top-Level-Felder.
- Freie Fehlertexte werden nicht über die API ausgegeben.

## Error Codes

Zulässige Fehlercodes:

- `INVALID_JSON`
- `INVALID_CONTENT_TYPE`
- `PAYLOAD_TOO_LARGE`
- `MISSING_FIELD`
- `UNKNOWN_ENDPOINT`
- `METHOD_NOT_ALLOWED`
- `INTERNAL_ERROR`

## Evaluate Success Data

`POST /evaluate` bettet Core-Ergebnisse strukturell ein:

```json
{
  "decision": "allow|deny|review|...",
  "stage": "core",
  "normalized_reason": {}
}
```

Der Normalizer interpretiert Entscheidungen nicht. Er übernimmt vorhandene Core-Felder und erzeugt daraus eine stabile API-Hülle.
