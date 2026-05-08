"""
WHY: Public pushes must not include runtime databases or generated simulation artifacts.
INV: This evidence only inspects repository hygiene; it does not mutate project state.
SEC: Generated DB files may contain local task/test data and must stay out of source control.
"""
from __future__ import annotations

from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
FORBIDDEN_ROOT_NAMES = {
    "gategraph.db",
    "gategraph.db-journal",
    "gategraph.db-wal",
    "gategraph.db-shm",
    "six_run_simulation_results.csv",
    "six_run_simulation_results_fixed.csv",
}
REQUIRED_IGNORE_PATTERNS = {
    "*.db",
    "/gategraph.db",
    "/six_run_simulation_results*.csv",
}


def main() -> int:
    failures: list[str] = []
    for name in sorted(FORBIDDEN_ROOT_NAMES):
        if (PROJECT_ROOT / name).exists():
            failures.append(f"forbidden root artifact present: {name}")

    gitignore = (PROJECT_ROOT / ".gitignore").read_text(encoding="utf-8")
    for pattern in sorted(REQUIRED_IGNORE_PATTERNS):
        if pattern not in gitignore:
            failures.append(f"missing .gitignore pattern: {pattern}")

    examples = [
        ("config.example.yaml", (PROJECT_ROOT / "config.example.yaml").read_text(encoding="utf-8")),
        ("task.example.json", (PROJECT_ROOT / "task.example.json").read_text(encoding="utf-8")),
    ]
    forbidden_fragments = ["sk-", "api_key:", "secret:", "https://", "http://"]
    for filename, text in examples:
        for fragment in forbidden_fragments:
            if fragment in text:
                failures.append(f"{filename} contains forbidden live-looking fragment: {fragment}")

    if failures:
        for failure in failures:
            print(f"FAIL {failure}")
        print(f"Summary: {{'passed': 0, 'failed': {len(failures)}}}")
        return 1

    print("✓ no root runtime database artifacts")
    print("✓ generated simulation CSV artifacts absent")
    print("✓ .gitignore protects DB and simulation artifacts")
    print("✓ example files contain no obvious secrets or live endpoints")
    print("PASS repo_push_hygiene_evidence")
    print("Summary: {'passed': 1, 'failed': 0}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
