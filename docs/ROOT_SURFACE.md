# Root Surface — v0.12.0_STABLE

The repository root is a public release surface. It should contain only high-signal project, release, security, and onboarding files.

Development-history artifacts and operational summaries are retained under `docs/release_artifacts/` when useful, but are not treated as root-level release truth.

## Root invariants

- Root files must not contradict release metadata.
- Root files must not contain generated runtime artifacts.
- Root files must not expose secrets, databases, logs, CSV simulations, or development prompts.
- Version/base/status claims must remain consistent with `RELEASE_METADATA.json`, `RELEASE_MANIFEST.json`, `VERSION.md`, release notes, and packaging evidence.
