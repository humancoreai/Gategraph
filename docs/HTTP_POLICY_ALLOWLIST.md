# HTTP Policy Allowlist (v0.8.12)

## Zweck

Der HTTP-Policy-Layer verhindert, dass kontrollierte API-Integrationen nach bestandener Governance-Pipeline beliebige Hosts, Pfade oder Methoden erreichen.

## Reihenfolge

Enforcement → Session Budget → Runtime Guard → HTTP Policy → Secret Provider → Transport

## Regeln

- Relative `/mock/`-Endpoints gelten als lokale deterministische Test-Seams.
- Netzwerkartige Endpoints müssen `https://` verwenden.
- Host, Pfadpräfix und Methode müssen in einer aktiven `api_endpoint_policies`-Regel erlaubt sein.
- Nicht erlaubte Endpoints stoppen vor Secret-Resolution und vor Transport.
- Audit speichert Policy-Status und Policy-ID, aber keine Secret-Werte.

## Grenzen

Das ist noch kein vollständiger HTTP-Sicherheitsstack. Es fehlen DNS/IP-Pinning, Redirect-Policy, Response-Schema-Validierung, Rate-Limit-Adapter und echte Client-Isolation.
