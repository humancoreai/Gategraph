# Architecture

## Components

- `risk_engine.py`: deterministic risk classification
- `rule_engine.py`: deterministic rule matching and conflict resolution
- `governance.py`: single entry point for evaluation
- `event_logger.py`: append-only, idempotent event writes
- `capability_token.py`: token issue helpers
- `enforcement.py`: hard gate before tool/action execution
- `database.py`: SQLite setup and seed rules
- `tests/test_loop.py`: isolated + accumulated validation loop

## Decision flow

```text
Task -> Risk -> Rule -> Decision -> Token -> Enforcement -> Event
```

## Audit graph

The PoC uses SQLite plus a simple `relations` adjacency table.

This is enough for MVP traceability, not meant as a complete graph database.
