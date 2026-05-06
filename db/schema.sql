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
    schema_version  TEXT NOT NULL DEFAULT '0.8.3',
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
    signature    TEXT NOT NULL DEFAULT '',
    signing_key_id TEXT NOT NULL DEFAULT 'local-dev-v1',
    budget_scope_id TEXT,
    budget_reservation_id TEXT,
    max_cost_for_action INTEGER,
    escalation_state TEXT,
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

-- Runtime Guard tables (v0.6)
CREATE TABLE IF NOT EXISTS runtime_budgets (
    budget_id TEXT PRIMARY KEY,
    task_id TEXT NOT NULL,
    max_steps INTEGER NOT NULL,
    max_runtime_seconds INTEGER NOT NULL,
    max_cost_units INTEGER NOT NULL,
    repeated_action_limit INTEGER NOT NULL,
    created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS runtime_steps (
    step_id TEXT PRIMARY KEY,
    task_id TEXT NOT NULL,
    step_index INTEGER NOT NULL,
    actor_id TEXT NOT NULL,
    action_type TEXT NOT NULL,
    action_signature TEXT NOT NULL,
    cost_units INTEGER NOT NULL,
    timestamp TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS runtime_decisions (
    decision_id TEXT PRIMARY KEY,
    task_id TEXT NOT NULL,
    step_id TEXT,
    decision TEXT NOT NULL,
    reason TEXT NOT NULL,
    created_at TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_runtime_steps_task
    ON runtime_steps(task_id);

CREATE INDEX IF NOT EXISTS idx_runtime_steps_signature
    ON runtime_steps(task_id, action_signature);

CREATE INDEX IF NOT EXISTS idx_runtime_decisions_task
    ON runtime_decisions(task_id);

-- Pattern Engine proposals (v0.7)
CREATE TABLE IF NOT EXISTS proposals (
    proposal_id TEXT PRIMARY KEY,
    schema_version TEXT NOT NULL DEFAULT '0.7',
    proposal_type TEXT NOT NULL,
    target_rule_id TEXT,
    reason TEXT NOT NULL,
    proposed_change TEXT NOT NULL,
    supporting_events TEXT NOT NULL,
    confidence REAL NOT NULL,
    confidence_basis TEXT NOT NULL,
    priority TEXT NOT NULL DEFAULT 'P3',
    score REAL NOT NULL DEFAULT 0,
    score_basis TEXT NOT NULL DEFAULT '',
    status TEXT NOT NULL DEFAULT 'pending_review',
    created_at TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_proposals_status
    ON proposals(status);

CREATE INDEX IF NOT EXISTS idx_proposals_target_rule
    ON proposals(target_rule_id);

CREATE INDEX IF NOT EXISTS idx_proposals_priority
    ON proposals(priority, score);


-- Session Budget Guard tables (v0.8)
CREATE TABLE IF NOT EXISTS session_budgets (
    session_id TEXT PRIMARY KEY,
    max_session_cost_units INTEGER NOT NULL,
    max_session_tasks INTEGER NOT NULL,
    max_agent_cost_units INTEGER NOT NULL,
    created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS session_task_links (
    session_id TEXT NOT NULL,
    task_id TEXT NOT NULL,
    actor_id TEXT NOT NULL,
    reserved_cost_units INTEGER NOT NULL DEFAULT 0,
    created_at TEXT NOT NULL,
    PRIMARY KEY (session_id, task_id)
);

CREATE TABLE IF NOT EXISTS session_budget_decisions (
    decision_id TEXT PRIMARY KEY,
    session_id TEXT NOT NULL,
    task_id TEXT NOT NULL,
    actor_id TEXT NOT NULL,
    projected_cost_units INTEGER NOT NULL,
    decision TEXT NOT NULL,
    reason TEXT NOT NULL,
    created_at TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_session_task_links_session
    ON session_task_links(session_id);

CREATE INDEX IF NOT EXISTS idx_session_task_links_actor
    ON session_task_links(session_id, actor_id);

CREATE INDEX IF NOT EXISTS idx_session_budget_decisions_session
    ON session_budget_decisions(session_id);

-- Secret references (v0.8.11)
-- SEC: raw secret values are never stored here; only provider references and scopes.
CREATE TABLE IF NOT EXISTS secret_refs (
    secret_ref_id TEXT PRIMARY KEY,
    provider TEXT NOT NULL,
    secret_name TEXT NOT NULL,
    allowed_endpoint_prefixes TEXT NOT NULL,
    allowed_capabilities TEXT NOT NULL,
    active INTEGER NOT NULL DEFAULT 1,
    created_at TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_secret_refs_active
    ON secret_refs(active);

-- API endpoint policies (v0.8.12)
-- SEC: real outbound HTTP endpoints are fail-closed unless host/path/method is explicitly allowlisted.
CREATE TABLE IF NOT EXISTS api_endpoint_policies (
    policy_id TEXT PRIMARY KEY,
    allowed_host TEXT NOT NULL,
    allowed_path_prefixes TEXT NOT NULL,
    allowed_methods TEXT NOT NULL,
    active INTEGER NOT NULL DEFAULT 1,
    created_at TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_api_endpoint_policies_active
    ON api_endpoint_policies(active);

-- Review workflow (v0.8.21)
-- INV: review decisions are human/process gates; they do not apply proposals automatically.
CREATE TABLE IF NOT EXISTS proposal_review_decisions (
    review_id TEXT PRIMARY KEY,
    proposal_id TEXT NOT NULL,
    reviewer_id TEXT NOT NULL,
    decision TEXT NOT NULL CHECK (decision IN ('approved_for_manual_action','rejected')),
    rationale TEXT NOT NULL,
    created_at TEXT NOT NULL,
    FOREIGN KEY (proposal_id) REFERENCES proposals(proposal_id)
);

CREATE INDEX IF NOT EXISTS idx_proposal_review_decisions_proposal
    ON proposal_review_decisions(proposal_id);

-- Controlled Apply (v0.8.22)
-- INV: apply requires separate two-person Human-Gate; artifacts are signed, TTL-bound, and single-use.
CREATE TABLE IF NOT EXISTS controlled_apply_reviews (
    review_id TEXT PRIMARY KEY,
    proposal_id TEXT NOT NULL,
    reviewer_id TEXT NOT NULL,
    decision TEXT NOT NULL CHECK (decision IN ('approved_for_controlled_apply','rejected')),
    rationale TEXT NOT NULL,
    created_at TEXT NOT NULL,
    FOREIGN KEY (proposal_id) REFERENCES proposals(proposal_id)
);

CREATE INDEX IF NOT EXISTS idx_controlled_apply_reviews_proposal
    ON controlled_apply_reviews(proposal_id);

CREATE TABLE IF NOT EXISTS controlled_apply_artifacts (
    artifact_id TEXT PRIMARY KEY,
    proposal_id TEXT NOT NULL,
    schema_version TEXT NOT NULL,
    change_type TEXT NOT NULL,
    change_json TEXT NOT NULL,
    before_json TEXT NOT NULL,
    artifact_hash TEXT NOT NULL UNIQUE,
    signing_key_id TEXT NOT NULL,
    signature TEXT NOT NULL,
    expires_at TEXT NOT NULL,
    created_at TEXT NOT NULL,
    status TEXT NOT NULL CHECK (status IN ('active','executed','expired','rejected')),
    executed_at TEXT,
    FOREIGN KEY (proposal_id) REFERENCES proposals(proposal_id)
);

CREATE INDEX IF NOT EXISTS idx_controlled_apply_artifacts_proposal
    ON controlled_apply_artifacts(proposal_id);


-- Cross-session Budget Ledger (v0.8.26 candidate)
-- SEC: budgets are reserved by Governance and only carried to Runtime through signed tokens.
CREATE TABLE IF NOT EXISTS budget_scopes (
    scope_id TEXT PRIMARY KEY,
    scope_type TEXT NOT NULL CHECK (scope_type IN ('system','actor','task','session')),
    parent_scope_id TEXT,
    allocated_units INTEGER NOT NULL CHECK (allocated_units >= 0),
    consumed_units INTEGER NOT NULL DEFAULT 0 CHECK (consumed_units >= 0),
    reserved_units INTEGER NOT NULL DEFAULT 0 CHECK (reserved_units >= 0),
    state TEXT NOT NULL DEFAULT 'normal' CHECK (state IN ('normal','degraded','throttled','blocked')),
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    reason_code TEXT NOT NULL DEFAULT 'BUDGET_SCOPE_CREATED',
    FOREIGN KEY (parent_scope_id) REFERENCES budget_scopes(scope_id)
);

CREATE TABLE IF NOT EXISTS budget_reservations (
    reservation_id TEXT PRIMARY KEY,
    scope_id TEXT NOT NULL,
    amount_units INTEGER NOT NULL CHECK (amount_units >= 0),
    status TEXT NOT NULL CHECK (status IN ('reserved','consumed','released','expired')),
    idempotency_key TEXT NOT NULL UNIQUE,
    created_at TEXT NOT NULL,
    expires_at TEXT NOT NULL,
    consumed_at TEXT,
    released_at TEXT,
    reason_code TEXT NOT NULL DEFAULT 'BUDGET_RESERVED',
    FOREIGN KEY (scope_id) REFERENCES budget_scopes(scope_id)
);

CREATE INDEX IF NOT EXISTS idx_budget_scopes_parent
    ON budget_scopes(parent_scope_id);
CREATE INDEX IF NOT EXISTS idx_budget_reservations_scope
    ON budget_reservations(scope_id, status);
CREATE INDEX IF NOT EXISTS idx_budget_reservations_idempotency
    ON budget_reservations(idempotency_key);
