# Public Repo Hygiene

Release: v0.15.4_STABLE  
Base: v0.14.7_STABLE  
Status: stable

This surface documents the minimal hygiene expected before public repository use.

## Scope

- Release, version, manifest and README surfaces must agree.
- Runtime databases, logs, local CI outputs and generated simulation artifacts must not be committed.
- Example configuration and task files must remain non-secret and local-example only.
- GitHub Actions is a read-only evidence runner and does not publish, deploy, auto-promote or mutate governance.
- Packaging remains deterministic and reviewable.

## Non-scope

- No new governance logic.
- No new runtime authority.
- No automatic policy repair.
- No external service dependency.
- No production deployment claim.

## Reviewer expectation

A fresh reviewer should be able to identify the current release, run the local evidence command, inspect the quickstart and understand the non-production deployment boundary without private project context.
