#!/usr/bin/env python3
"""
Release Process Guard.

WHY: Candidate/Stable promotion drift is a release-integrity failure.
INV: This tool validates release truth only; it does not modify governance, runtime, adapters, or policy.
SEC: Ambiguous release claims, stale manifests, and dead current references fail closed.
"""
from __future__ import annotations

import hashlib
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

RELEASE_FILES = [
    "RELEASE_STATUS.md",
    "RELEASE_METADATA.json",
    "RELEASE_NOTES.md",
    "VERSION.md",
    "docs/DEPLOYMENT_BOUNDARY.md",
    "tests/config_consistency_evidence.py",
    "tests/startup_surface_evidence.py",
    "docs/STARTUP_SURFACE.md",
    "pyproject.toml",
    "README.md",
    "CHANGELOG.md",
    "docs/KNOWN_GAPS_ROADMAP.md",
    "docs/SERVER_MODE.md",
    "docs/ARCHITECTURE.md",
    "ARCHITECTURE.md",
    "PRODUCTION.md",
    "tests/release_integrity_evidence.py",
    "tests/milestone_release_evidence.py",
    "tests/final_consolidation_evidence.py",
    "tools/build_release.py",
    "tools/verify_release.py",
]

LOCAL_REF_RE = re.compile(r"`((?:docs|tests|src|tools)/[^`]+?)`")


def ok(name: str, detail: str = "ok") -> dict:
    return {"name": name, "ok": True, "detail": detail}


def fail(name: str, detail: str) -> dict:
    return {"name": name, "ok": False, "detail": detail}


def check_release_truth(expected_release: str, expected_status: str, expected_base: str | None) -> dict:
    problems: list[str] = []

    for rel in RELEASE_FILES:
        path = ROOT / rel
        if not path.exists():
            problems.append(f"missing release surface: {rel}")
            continue
        text = path.read_text(encoding="utf-8")
        if expected_release not in text:
            problems.append(f"{rel} does not mention {expected_release}")

    metadata_path = ROOT / "RELEASE_METADATA.json"
    if metadata_path.exists():
        try:
            metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
        except json.JSONDecodeError as exc:
            problems.append(f"RELEASE_METADATA.json invalid JSON: {exc}")
        else:
            if metadata.get("release") != expected_release:
                problems.append(f"metadata release={metadata.get('release')!r}, expected {expected_release!r}")
            if metadata.get("status") != expected_status:
                problems.append(f"metadata status={metadata.get('status')!r}, expected {expected_status!r}")
            if expected_base is not None and metadata.get("base") != expected_base:
                problems.append(f"metadata base={metadata.get('base')!r}, expected {expected_base!r}")

    if expected_status == "stable" and "_CANDIDATE" in expected_release:
        forbidden = expected_release.replace("_CANDIDATE", "_STABLE")
        for rel in RELEASE_FILES:
            path = ROOT / rel
            if not path.exists():
                continue
            text = path.read_text(encoding="utf-8")
            forbidden_status_label = "Status: " + "stable"
            forbidden_current_label = "Current " + "stable:"
            forbidden_current_baseline = "Current " + "stable baseline:"
            if (
                f'"release": "{forbidden}"' in text
                or f'VERSION = "{forbidden}"' in text
                or forbidden_status_label in text
                or forbidden_current_label in text
                or forbidden_current_baseline in text
            ):
                problems.append(f"{rel} contains stable claim while expected status is not stable")

    return fail("release_truth", "; ".join(problems)) if problems else ok("release_truth")


def check_manifest(expected_release: str, expected_base: str | None) -> dict:
    path = ROOT / "RELEASE_MANIFEST.json"
    if not path.exists():
        return fail("manifest", "RELEASE_MANIFEST.json missing")

    try:
        manifest = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        return fail("manifest", f"invalid JSON: {exc}")

    problems: list[str] = []
    if not isinstance(manifest, dict) or not isinstance(manifest.get("files"), list):
        return fail("manifest", "manifest must be structured with release/base/files")

    if manifest.get("release") != expected_release:
        problems.append(f"manifest release={manifest.get('release')!r}, expected {expected_release!r}")
    if expected_base is not None and manifest.get("base") != expected_base:
        problems.append(f"manifest base={manifest.get('base')!r}, expected {expected_base!r}")
    if manifest.get("deterministic_packaging") is not True:
        problems.append("manifest deterministic_packaging must be true")

    entries = manifest["files"]
    by_path = {entry.get("path"): entry for entry in entries if isinstance(entry, dict)}
    paths = list(by_path)
    if paths != sorted(paths):
        problems.append("manifest paths are not sorted")

    actual_paths: set[str] = set()
    for item in sorted(ROOT.rglob("*")):
        if not item.is_file():
            continue
        rel = item.relative_to(ROOT).as_posix()
        if rel == "RELEASE_MANIFEST.json":
            continue
        if (
            rel == "ARTIFACTS.sha256"
            or rel.startswith(".git/")
            or rel.startswith(".github/_temp/")
            or rel.startswith("dist/")
            or rel.startswith("tests/logs/")
            or "__pycache__" in rel
            or rel.endswith((".pyc", ".pyo", ".db", ".csv", ".zip", ".log", ".tmp"))
        ):
            continue
        actual_paths.add(rel)
        entry = by_path.get(rel)
        if entry is None:
            problems.append(f"missing manifest entry: {rel}")
            continue
        data = item.read_bytes()
        if entry.get("sha256") != hashlib.sha256(data).hexdigest():
            problems.append(f"sha mismatch: {rel}")
        if entry.get("size") != len(data):
            problems.append(f"size mismatch: {rel}")

    for stale in sorted(set(by_path) - actual_paths):
        if stale == "RELEASE_MANIFEST.json":
            continue
        problems.append(f"stale manifest entry: {stale}")

    return fail("manifest", "; ".join(problems[:30])) if problems else ok("manifest")


def check_dead_refs() -> dict:
    problems: list[str] = []
    ignored = 0

    for md in sorted(ROOT.rglob("*.md")):
        doc_rel = md.relative_to(ROOT).as_posix()
        text = md.read_text(encoding="utf-8")
        for match in LOCAL_REF_RE.finditer(text):
            ref = match.group(1).strip().split("#", 1)[0]
            if not ref:
                continue
            if "*" in ref or ref.endswith("/") or ref.startswith("tests/logs/") or "/logs/" in ref:
                ignored += 1
                continue
            if not (ROOT / ref).exists():
                problems.append(f"{doc_rel} references missing {ref}")

    if problems:
        return fail("dead_refs", "; ".join(problems[:25]))
    detail = "ok" if ignored == 0 else f"ok; ignored generated/log refs: {ignored}"
    return ok("dead_refs", detail)



def check_document_version_surfaces(expected_release: str) -> dict:
    problems: list[str] = []

    changelog = ROOT / "CHANGELOG.md"
    if changelog.exists():
        text = changelog.read_text(encoding="utf-8")
        current_headers = re.findall(r"^##\s+" + re.escape(expected_release) + r"\s*$", text, flags=re.MULTILINE)
        if len(current_headers) != 1:
            problems.append(f"CHANGELOG current release header count={len(current_headers)}, expected 1")
    else:
        problems.append("CHANGELOG.md missing")

    known = ROOT / "docs" / "KNOWN_GAPS_ROADMAP.md"
    if known.exists():
        text = known.read_text(encoding="utf-8")
        if expected_release not in text:
            problems.append("KNOWN_GAPS_ROADMAP.md does not mention current release")
        if "No pip package / `pyproject.toml` packaging baseline" in text:
            problems.append("KNOWN_GAPS_ROADMAP.md still lists pyproject.toml packaging baseline as open")
        if "v0.10.0_STABLE" in text.splitlines()[0]:
            problems.append("KNOWN_GAPS_ROADMAP.md title is stale")
    else:
        problems.append("docs/KNOWN_GAPS_ROADMAP.md missing")

    server = ROOT / "src" / "server.py"
    if server.exists():
        text = server.read_text(encoding="utf-8")
        expected_http_version = expected_release.replace("_STABLE", "").replace("_STABLE", "")
        if f'GateGraphHTTP/{expected_http_version}' not in text:
            problems.append(f"src/server.py server_version does not match {expected_http_version}")
    else:
        problems.append("src/server.py missing")

    return fail("document_version_surfaces", "; ".join(problems)) if problems else ok("document_version_surfaces")


def check_public_surface_contracts() -> dict:
    problems: list[str] = []

    readme = ROOT / "README.md"
    if readme.exists():
        text = readme.read_text(encoding="utf-8")
        if len(re.findall(r"^Base stable:", text, flags=re.MULTILINE)) > 1:
            problems.append("README.md contains multiple Base stable claims")
        if len(re.findall(r"^Base:", text, flags=re.MULTILINE)) > 1:
            problems.append("README.md contains multiple Base claims")

    risk_engine = ROOT / "src" / "risk_engine.py"
    trust_model = ROOT / "TRUST_MODEL.md"
    if risk_engine.exists() and trust_model.exists():
        src = risk_engine.read_text(encoding="utf-8")
        match = re.search(r"VALID_INPUT_SOURCES\s*=\s*\{([^}]+)\}", src)
        if not match:
            problems.append("src/risk_engine.py does not expose VALID_INPUT_SOURCES")
        else:
            code_values = set(re.findall(r"['\"]([^'\"]+)['\"]", match.group(1)))
            tm = trust_model.read_text(encoding="utf-8")
            documented = set(re.findall(r"`(local|external|untrusted|trusted)`", tm))
            # SEC: `trusted` is a trust-level/context word, not a valid input_source unless code supports it.
            if "trusted" in documented and "not a valid `input_source`" not in tm and "trusted" not in code_values:
                problems.append("TRUST_MODEL.md documents trusted as input_source but risk_engine.py does not support it")
            for value in code_values:
                if f"`{value}`" not in tm:
                    problems.append(f"TRUST_MODEL.md does not document input_source={value!r}")

    return fail("public_surface_contracts", "; ".join(problems)) if problems else ok("public_surface_contracts")


def run(expected_release: str, expected_status: str, expected_base: str | None) -> dict:
    checks = [
        check_release_truth(expected_release, expected_status, expected_base),
        check_manifest(expected_release, expected_base),
        check_dead_refs(),
        check_document_version_surfaces(expected_release),
        check_public_surface_contracts(),
    ]
    return {
        "expected_release": expected_release,
        "expected_status": expected_status,
        "expected_base": expected_base,
        "passed": all(check["ok"] for check in checks),
        "checks": checks,
    }


def main(argv: list[str]) -> int:
    expected_release = argv[1] if len(argv) > 1 else "v0.12.0_STABLE"
    expected_status = argv[2] if len(argv) > 2 else "stable"
    expected_base = argv[3] if len(argv) > 3 else None
    result = run(expected_release, expected_status, expected_base)
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0 if result["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
