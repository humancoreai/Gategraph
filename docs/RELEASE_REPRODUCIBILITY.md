# Release Reproducibility

## Goal

GateGraph releases must be reproducible enough for review: stable file selection, deterministic manifest ordering, checksum output, and explicit exclusion of runtime artifacts.

## Requirements

Release packages must not include:

- `.db` files,
- CSV runtime artifacts,
- temporary files,
- caches,
- test logs,
- generated local runtime state.

## Required artifacts

- release ZIP,
- SHA256 checksum,
- `RELEASE_MANIFEST.json`,
- `RELEASE_METADATA.json`,
- release notes/status.

## Boundary

Release reproducibility validates packaging and reviewability. It does not validate correctness by itself; correctness remains evidence-driven.
