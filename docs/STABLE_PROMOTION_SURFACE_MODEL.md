# Stable Promotion Surface Model

Release: v0.16.7_STABLE  
Base: v0.16.7_STABLE  
Status: stable  
Mode: descriptive evidence only

## Purpose

This model defines how Candidate and Stable public surfaces are checked during manual promotion.

## Boundary

Candidate surfaces may reference the previous stable base, but must not claim the future stable token as the current release. After promotion, Stable surfaces may legitimately claim the stable token as current release.

## v0.16.0 hardening

The evidence is status-sensitive:

- Candidate mode: future-Stable current-release claims are blocked.
- Stable mode: current-Stable claims are legitimate release truth.
- The check remains descriptive only and has no runtime, repair, promotion, or policy authority.

## Non-scope

- No auto-promotion.
- No auto-repair.
- No governance mutation.
- No runtime authority.
