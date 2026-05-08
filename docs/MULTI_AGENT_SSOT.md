# Multi-Agent SSOT — v0.9.2_STABLE

## Status

This document is architectural SSOT only. It does not introduce autonomous agents or distributed governance.

## Agent Definition

An Agent is a runtime identity bound to a governed task context.

An Agent may be represented by:

- agent_id: stable runtime identity within a trace
- parent_agent_id: optional lineage reference
- task_id: governed task binding
- mode_id: selected runtime/capability profile
- budget_scope_id: externally granted budget scope
- capability_context_id: narrowed capability context
- trace_id: audit/replay lineage root

## What an Agent Is Not

An Agent is not:

- not a policy authority
- a governance participant
- not a budget owner
- a self-elevating actor
- a hidden communication channel
- a rule writer
- an autonomous orchestrator

## Authority Boundary

Agents may request work only through existing governance and enforcement gates. Every delegated action must receive an explicit decision and capability token.

## Central Invariant

Governance remains central. Agents execute only inside externally granted, narrowed, auditable contexts.
