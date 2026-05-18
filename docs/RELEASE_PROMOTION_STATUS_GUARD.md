# Release Promotion Status Guard

Release: v0.17.6_CANDIDATE  
Base: v0.17.6_CANDIDATE  
Status: stable

## Purpose

This release adds a descriptive release guard for promotion status drift.

The guard checks that release metadata and registry/profile surfaces agree on:

- release token
- base token
- status token
- future stable token where declared

## Scope

This is release/process evidence only.

It does not change runtime governance, enforcement, policy evaluation, token issuance, budget behavior, or operator authority.

## Non-authority

The guard is read-only. It does not repair, promote, prune, or mutate registry state.
