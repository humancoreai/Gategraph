from __future__ import annotations

import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SNAPSHOT_PATHS = [
    "registry/schema_governance_registry.json",
    "registry/semantic_object_types.json",
    "registry/invariant_surface_registry.json",
    "registry/semantic_registry_lock.json",
    "RELEASE_METADATA.json",
]


def file_hash(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def build_snapshot() -> dict:
    entries = [{"path": p, "sha256": file_hash(ROOT / p)} for p in sorted(SNAPSHOT_PATHS)]
    digest = hashlib.sha256(json.dumps(entries, sort_keys=True, separators=(",", ":")).encode("utf-8")).hexdigest()
    return {"snapshot_mode": "deterministic_freeze_reconstruction", "runtime_authority": False, "entries": entries, "freeze_hash": digest}


def check(name: str, ok: bool, detail: dict) -> tuple[str, bool, dict]:
    print(("✓" if ok else "✗") + f" {name}: {detail}")
    return name, ok, detail


def main() -> int:
    checks = []
    first = build_snapshot()
    second = build_snapshot()
    checks.append(check("freeze_reconstruction_deterministic", first == second, {"freeze_hash": first["freeze_hash"]}))
    missing = [p for p in SNAPSHOT_PATHS if not (ROOT / p).exists()]
    checks.append(check("freeze_snapshot_paths_exist", not missing, {"missing": missing}))
    checks.append(check("freeze_snapshot_non_authoritative", first["runtime_authority"] is False, {"runtime_authority": first["runtime_authority"]}))
    entries = [e["path"] for e in first["entries"]]
    checks.append(check("freeze_entries_sorted", entries == sorted(entries), {"entries": entries}))
    failed = [name for name, ok, _ in checks if not ok]
    print("Summary:", {"passed": len(checks) - len(failed), "failed": len(failed), "failed_checks": failed})
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
