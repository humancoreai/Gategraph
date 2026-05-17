"""
WHY: Public repository readiness needs deterministic checks, not prose-only claims.
INV: This evidence is read-only and never repairs repository state.
SEC: Local artifacts, secrets and publish/deploy authority are rejected fail-closed.
"""
from __future__ import annotations

import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RELEASE = "v0.16.0_STABLE"
BASE = "v0.15.9_STABLE"
VERSION = "0.14.8"

FORBIDDEN_ROOT_ARTIFACTS = {
    "gategraph.db",
    "gategraph.db-journal",
    "gategraph.db-wal",
    "gategraph.db-shm",
}
FORBIDDEN_SUFFIXES = {".db", ".csv", ".log", ".tmp", ".temp", ".zip"}
SECRET_PATTERNS = [
    re.compile(r"sk-[A-Za-z0-9_-]{20,}"),
    re.compile(r"AKIA[0-9A-Z]{16}"),
    re.compile(r"(?i)(api[_-]?key|secret|token)\s*=\s*['\"][^'\"]{12,}['\"]"),
]
REQUIRED_PUBLIC_SURFACES = [
    "README.md",
    "LICENSE",
    "SECURITY.md",
    "CONTRIBUTING.md",
    "KNOWN_LIMITATIONS.md",
    "PRODUCTION.md",
    "docs/QUICKSTART.md",
    "docs/PUBLIC_REPO_HYGIENE.md",
    "docs/GITHUB_ACTIONS_CI.md",
    "docs/RELEASE_v0.16.0_STABLE.md",
]


def check(name: str, ok: bool, detail: object | None = None, failures: list[str] | None = None) -> None:
    if ok:
        print(f"✓ {name}: {detail or {}}")
    else:
        print(f"✗ {name}: {detail or {}}")
        if failures is not None:
            failures.append(name)


def read(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8")


def main() -> int:
    failures: list[str] = []
    metadata = json.loads(read("RELEASE_METADATA.json"))
    manifest = json.loads(read("RELEASE_MANIFEST.json"))

    check(
        "metadata_candidate_public_hygiene_scope",
        metadata.get("release") == RELEASE
        and metadata.get("base") == BASE
        and metadata.get("status") == "stable"
        and metadata.get("public_repo_hygiene_scope") is True
        and metadata.get("quickstart_surface_scope") is True,
        {"release": metadata.get("release"), "base": metadata.get("base"), "status": metadata.get("status")},
        failures,
    )
    check(
        "manifest_candidate_state",
        manifest.get("release") == RELEASE and manifest.get("base") == BASE and manifest.get("status") == "stable",
        {"release": manifest.get("release"), "base": manifest.get("base"), "status": manifest.get("status")},
        failures,
    )

    missing = [p for p in REQUIRED_PUBLIC_SURFACES if not (ROOT / p).is_file()]
    check("required_public_surfaces_present", not missing, {"missing": missing}, failures)

    quickstart = read("docs/QUICKSTART.md")
    check(
        "quickstart_has_reproducible_commands",
        "python -m pip install -e ." in quickstart and "python tests\\evidence_ci.py" in quickstart,
        {},
        failures,
    )

    gha = read(".github/workflows/evidence_ci.yml")
    forbidden_workflow_terms = ["secrets.", "docker/login-action", "gh release", "twine upload", "pypi"]
    found_workflow_terms = [term for term in forbidden_workflow_terms if term in gha]
    check("github_actions_no_publish_or_secret_surface", not found_workflow_terms, {"found": found_workflow_terms}, failures)
    check("github_actions_read_only", "contents: read" in gha and "write" not in gha.lower(), {}, failures)

    gitignore = read(".gitignore")
    required_ignores = ["*.db", "*.csv", "tests/logs/", "dist/", ".vscode/", ".idea/"]
    missing_ignores = [entry for entry in required_ignores if entry not in gitignore]
    check("gitignore_blocks_local_artifacts", not missing_ignores, {"missing": missing_ignores}, failures)

    generated_artifacts: list[str] = []
    for path in ROOT.rglob("*"):
        if not path.is_file():
            continue
        rel = path.relative_to(ROOT).as_posix()
        if rel.startswith("dist/"):
            continue
        if rel == "tests/logs/.gitkeep":
            continue
        # CI creates evidence logs during this same aggregate run; .gitignore prevents repo publication.
        if rel.startswith("tests/logs/"):
            continue
        if path.name in FORBIDDEN_ROOT_ARTIFACTS:
            generated_artifacts.append(rel)
        if path.suffix.lower() in FORBIDDEN_SUFFIXES and rel != ".gitignore":
            if not rel.startswith("docs/release_artifacts/"):
                generated_artifacts.append(rel)
    check("generated_local_artifacts_absent", not generated_artifacts, {"found": generated_artifacts[:10]}, failures)

    secret_hits: list[str] = []
    for rel in ["config.example.yaml", "task.example.json", "README.md", "docs/QUICKSTART.md"]:
        text = read(rel)
        for pattern in SECRET_PATTERNS:
            if pattern.search(text):
                secret_hits.append(rel)
                break
    check("examples_and_public_docs_have_no_obvious_live_secrets", not secret_hits, {"hits": secret_hits}, failures)

    public_doc = read("docs/PUBLIC_REPO_HYGIENE.md")
    check(
        "public_hygiene_declares_non_authority",
        "No new governance logic" in public_doc
        and "No new runtime authority" in public_doc
        and "does not publish, deploy, auto-promote or mutate governance" in public_doc,
        {},
        failures,
    )

    result = {"passed": len(failures) == 0, "failed_checks": failures}
    print("PUBLIC REPO HYGIENE EVIDENCE REPORT")
    print(result)
    return 0 if not failures else 1


if __name__ == "__main__":
    raise SystemExit(main())
