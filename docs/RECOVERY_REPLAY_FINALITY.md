# Recovery Replay Finality

Release: v0.17.3_CANDIDATE  
Base: v0.14.7_STABLE  
Status: candidate  
Scope: Recovery Replay Finality Hardening.

## Purpose

This document defines the v0.14.6 recovery/replay finality surface. The scope is evidence-only hardening around already existing recovery behavior:

- duplicate recovery attempts remain idempotent and descriptive;
- consumed/released reservations remain final;
- conflicting audit-derived finality fails closed;
- replay and recovery snapshots remain reference-only;
- no repair, rehydration, policy mutation, runtime authority or capability creation is introduced.

## Non-scope

- no governance logic change;
- no enforcement logic change;
- no runtime model change;
- no autonomous repair;
- no replay-to-runtime promotion;
- no policy learning or semantic scoring.

## Evidence

Validated by `tests/recovery_replay_finality_evidence.py`.
