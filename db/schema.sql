-- INV: append-only — no DELETE, no UPDATE on events ever
-- WHY: audit integrity requires immutable event history

PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS tasks (
    task_id          TEXT PRIMARY KEY,
    task_type        TEXT NOT NULL,
    capabilities     TEXT NOT NULL,
    input_source     TEXT NOT NULL,
    data_sensitivity TEXT NOT NULL DEFAULT 'internal',
    secrets_involved INTEGER NOT NULL DEFAULT 0,
    created_at       TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS rules (
    rule_id         TEXT PRIMARY KEY,
    version         TEXT NOT NULL DEFAULT '1.0.0',
    scope           TEXT NOT NULL,
    trigger_caps    TEXT NOT NULL,
    risk_threshold  TEXT NOT NULL CHECK (risk_threshold IN ('low','medium','high','critical')),
    severity        TEXT NOT NULL CHECK (severity IN ('low','medium','high','critical')),
    decision        TEXT NOT NULL CHECK (decision IN ('allow','warn','require_review','require_approval','block')),
    priority        INTEGER NOT NULL DEFAULT 10,
    rationale       TEXT NOT NULL,
    active          INTEGER NOT NULL DEFAULT 1,
    created_at      TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS events (
    event_id        TEXT PRIMARY KEY,
    schema_version  TEXT NOT NULL DEFAULT '0.4',
    idempotency_key TEXT NOT NULL,
    correlation_id  TEXT NOT NULL,
    causation_id    TEXT,
    type            TEXT NOT NULL,
    timestamp       TEXT NOT NULL,
    task_id         TEXT NOT NULL,
    actor_layer     TEXT NOT NULL,
    actor_component TEXT NOT NULL,
    actor_version   TEXT NOT NULL,
    input_json      TEXT NOT NULL,
    evaluation_json TEXT NOT NULL,
    decision_json   TEXT NOT NULL,
    FOREIGN KEY (task_id) REFERENCES tasks(task_id)
);

-- INV: idempotency_key must be globally unique
-- SEC: prevents duplicate event injection via replay
CREATE UNIQUE INDEX IF NOT EXISTS idx_events_idempotency ON events(idempotency_key);

CREATE TABLE IF NOT EXISTS decisions (
    decision_id        TEXT PRIMARY KEY,
    task_id            TEXT NOT NULL,
    event_id           TEXT NOT NULL,
    status             TEXT NOT NULL,
    final_caps_json    TEXT NOT NULL,
    reason             TEXT NOT NULL,
    matched_rules_json TEXT NOT NULL,
    created_at         TEXT NOT NULL,
    FOREIGN KEY (task_id) REFERENCES tasks(task_id),
    FOREIGN KEY (event_id) REFERENCES events(event_id)
);

CREATE TABLE IF NOT EXISTS capability_tokens (
    token_id     TEXT PRIMARY KEY,
    decision_id  TEXT NOT NULL,
    task_id      TEXT NOT NULL,
    capabilities TEXT NOT NULL,
    issued_at    TEXT NOT NULL,
    expires_at   TEXT NOT NULL,
    revoked      INTEGER NOT NULL DEFAULT 0,
    FOREIGN KEY (decision_id) REFERENCES decisions(decision_id),
    FOREIGN KEY (task_id) REFERENCES tasks(task_id)
);

-- WHY: simple adjacency list is sufficient for MVP graph traversal
CREATE TABLE IF NOT EXISTS relations (
    id           INTEGER PRIMARY KEY AUTOINCREMENT,
    subject_id   TEXT NOT NULL,
    subject_type TEXT NOT NULL,
    relation     TEXT NOT NULL,
    object_id    TEXT NOT NULL,
    object_type  TEXT NOT NULL,
    created_at   TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_relations_subject ON relations(subject_id, subject_type);
CREATE INDEX IF NOT EXISTS idx_relations_object  ON relations(object_id, object_type);
