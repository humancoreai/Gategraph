# REPO_HYGIENE.md

## v0.8.34_STABLE package hygiene

This archive is intended as a clean repo snapshot.

Included:

- `src/` production/prototype source files
- `tests/` full evidence suite
- `db/schema.sql`
- `docs/` release, architecture and evidence documentation
- root docs: README, SECURITY, GOVERNANCE, ARCHITECTURE, PRODUCTION, RELEASE notes/status, VERSION
- `.github/workflows/evidence.yml`
- example config/task files

Excluded by `.gitignore` / packaging hygiene:

- Python bytecode and `__pycache__`
- local databases and SQLite journal/WAL/SHM files
- generated evidence logs
- temporary files
- virtual environments
- OS/editor noise

Stable promotion note:

- Full Windows Evidence CI for v0.8.34 passed before this stable consolidation.
