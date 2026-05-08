import os
import subprocess
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
LOG_DIR = PROJECT_ROOT / "evidence_logs"

def _kill_process_group(proc):
    if os.name == "nt":
        subprocess.run(["taskkill", "/PID", str(proc.pid), "/T", "/F"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        return True
    else:
        try:
            os.killpg(proc.pid, 9)
            return True
        except Exception:
            return False

def run_one(name: str, script: str, timeout_seconds: int):
    LOG_DIR.mkdir(exist_ok=True)
    out_path = LOG_DIR / f"{name}.stdout.log"
    err_path = LOG_DIR / f"{name}.stderr.log"

    env = os.environ.copy()
    env["PYTHONUTF8"] = "1"

    cmd = ["python", "tests/_run_isolated.py", script]

    timed_out = False
    killed_group = False
    rc = None

    with out_path.open("wb") as out, err_path.open("wb") as err:
        creationflags = 0
        if os.name == "nt":
            creationflags = subprocess.CREATE_NEW_PROCESS_GROUP

        proc = subprocess.Popen(
            cmd,
            cwd=PROJECT_ROOT,
            env=env,
            text=False,
            stdout=out,
            stderr=err,
            start_new_session=(os.name == "posix"),
            creationflags=creationflags,
        )

        try:
            rc = proc.wait(timeout=timeout_seconds)
        except subprocess.TimeoutExpired:
            timed_out = True
            killed_group = _kill_process_group(proc)
            try:
                rc = proc.wait(timeout=2.0)
            except subprocess.TimeoutExpired:
                rc = 124

    return {
        "name": name,
        "rc": rc,
        "timed_out": timed_out,
        "killed_group": killed_group,
    }

if __name__ == "__main__":
    tests = [
        ("runner_selftest", "tests/evidence_runner_selftest.py", 10),
    ]

    results = []
    for name, script, timeout in tests:
        print(f"--- {name} ---")
        res = run_one(name, script, timeout)
        print(res)
        results.append(res)

    passed = sum(1 for r in results if r["rc"] == 0)
    failed = len(results) - passed

    print(f"Summary: {{'passed': {passed}, 'failed': {failed}}}")
