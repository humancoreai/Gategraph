# Evidence Profile Runtime Profiles

Release: v0.16.6_STABLE  
Base: v0.16.5_STABLE  
Status: stable

## Purpose

This phase makes Evidence CI overlap visible before any pruning or merging.

## Invariant

Evidence cleanup is descriptive only. It must not remove gates, lower criticality, mutate policy, or change runtime governance behavior.

## Current finding

GateGraph carries several intentionally overlapping evidence groups:

- release / surface / version consistency
- artifact and fresh-clone reproducibility
- semantic, context, replay and reference-boundary tests

These overlaps are not automatically bad. Some are safety nets against release drift. The cleanup goal is to separate exclusive coverage from duplicate assertions before any later simplification.

## Non-scope

- no automatic pruning
- no test removal in this candidate
- no runtime or governance logic change
- no Multi-Node implementation
