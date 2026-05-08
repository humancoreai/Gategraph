<!-- v0.9.1_CANDIDATE note: Boundary hardening and release integrity closure; no governance logic expansion. -->

# Release Content Rules

## Purpose

Official v0.9.0 release packages must be reproducible and reviewable. Packaging is part of release integrity, not a manual afterthought.

## Included content

- source code under `src/`
- tests and evidence scripts under `tests/`
- documentation and review files
- example configuration/task files
- release metadata and manifest files
- packaging/verification tools

## Excluded content

- hidden files and directories except the required root `.gitignore`
- `.git/` metadata
- `__pycache__/`
- `*.pyc`
- SQLite runtime databases (`*.db`, `*.db-wal`, `*.db-shm`, `*.db-journal`)
- generated CSV artifacts
- generated logs except intentional placeholders
- previous ZIP archives

## Deterministic ZIP rules

- entries sorted lexicographically
- fixed ZIP timestamp for all entries
- normalized POSIX path separators
- no absolute paths
- no platform-specific metadata requirements
- manifest generated from the exact included file set
- root `.gitignore` is included as a repository-hygiene control file, not as hidden local state
