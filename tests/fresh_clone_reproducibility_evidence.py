"""
WHY: v0.14.6 checks that a fresh clone has enough deterministic onboarding surface to run evidence.
INV: This evidence is read-only; it does not install packages, mutate policy, or promote releases.
SEC: Reproducibility claims must not depend on secrets, publish steps, or generated local artifacts.
"""
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RELEASE = "v0.16.4_CANDIDATE"
BASE = "v0.16.3_STABLE"
VERSION = "0.16.4"

REQUIRED = [
    "README.md",
    "pyproject.toml",
    "config.example.yaml",
    "task.example.json",
    "docs/QUICKSTART.md",
    "docs/FRESH_CLONE_REPRODUCIBILITY.md",
    "docs/PUBLIC_REPO_HYGIENE.md",
    "tests/evidence_ci.py",
    "tests/install_surface_evidence.py",
    "tests/public_repo_hygiene_evidence.py",
]

FORBIDDEN_TERMS = ["twine upload", "gh release", "docker/login-action", "secrets."]


def read(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8")


def check(name: str, ok: bool, detail: object | None, failures: list[str]) -> None:
    if ok:
        print(f"✓ {name}: {detail or {}}")
    else:
        print(f"✗ {name}: {detail or {}}")
        failures.append(name)


def main() -> int:
    failures: list[str] = []
    metadata = json.loads(read("RELEASE_METADATA.json"))
    manifest = json.loads(read("RELEASE_MANIFEST.json"))
    paths = {entry["path"] for entry in manifest.get("files", [])}

    check(
        "metadata_current_stable",
        metadata.get("release") == RELEASE and metadata.get("base") == BASE and metadata.get("status") == "candidate",
        {"release": metadata.get("release"), "base": metadata.get("base"), "status": metadata.get("status")},
        failures,
    )
    check(
        "manifest_current_stable",
        manifest.get("release") == RELEASE and manifest.get("base") == BASE and manifest.get("status") == "candidate",
        {"release": manifest.get("release"), "base": manifest.get("base"), "status": manifest.get("status")},
        failures,
    )

    missing = [p for p in REQUIRED if not (ROOT / p).is_file()]
    check("fresh_clone_required_files_present", not missing, {"missing": missing}, failures)

    missing_manifest = [p for p in REQUIRED if p not in paths]
    check("fresh_clone_required_files_manifested", not missing_manifest, {"missing": missing_manifest}, failures)

    quickstart = read("docs/QUICKSTART.md") + "\n" + read("docs/FRESH_CLONE_REPRODUCIBILITY.md")
    check(
        "fresh_clone_commands_documented",
        "python -m pip install -e ." in quickstart and "python tests\\evidence_ci.py" in quickstart,
        {},
        failures,
    )

    pyproject = read("pyproject.toml")
    check(
        "package_version_current",
        f'version = "{VERSION}"' in pyproject and 'gategraph = "src.cli:main"' in pyproject,
        {},
        failures,
    )

    workflow = read(".github/workflows/evidence_ci.yml")
    forbidden = [term for term in FORBIDDEN_TERMS if term in workflow]
    check("fresh_clone_ci_has_no_publish_or_secret_surface", not forbidden, {"found": forbidden}, failures)

    doc = read("docs/FRESH_CLONE_REPRODUCIBILITY.md")
    check(
        "fresh_clone_declares_non_authority",
        "No new governance logic" in doc and "No runtime authority" in doc and "No auto-promotion" in doc,
        {},
        failures,
    )

    result = {"passed": not failures, "failed_checks": failures}
    print("FRESH CLONE REPRODUCIBILITY EVIDENCE REPORT")
    print(result)
    return 0 if not failures else 1


if __name__ == "__main__":
    raise SystemExit(main())
