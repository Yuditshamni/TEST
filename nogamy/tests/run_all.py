"""Every offline test of the core, in one command (core CI runs it on every PR). Standard library only.

    python nogamy/tests/run_all.py

| Test | Proves |
|---|---|
| test_hook.py | the hook: core lock, skill gate, base_prompt by section, each tool's event shape, a hook bug never blocks |
| test_migrations.py | tools/run_migrations.py offline: SQL split per dialect, full run on SQLite, re-run, failure, DROP/PROD refused |
| test_sync.py | template -> project -> core update: packs, stored copies, checksums |
| test_guard.py | release -> project -> core edit caught -> undone -> newer core arrives and passes the PR check |
| test_upgrades.py | project files adapted on a core update: safe twice, never a core file, a failure stops |
test_migrations_live.py needs a database (core CI starts Postgres and SQL Server); not run here.
"""
import subprocess
import sys
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
TESTS = ["test_hook.py", "test_migrations.py", "test_sync.py", "test_guard.py", "test_upgrades.py"]


def main():
    failed = []
    for t in TESTS:
        start = time.time()
        r = subprocess.run([sys.executable, str(HERE / t)], capture_output=True, text=True, encoding="utf-8")
        lines = (r.stdout + r.stderr).splitlines()
        passed = sum(1 for x in lines if x.startswith("PASS "))
        bad = [x for x in lines if x.startswith("FAIL ")]
        status = "ok  " if r.returncode == 0 else "FAIL"
        print(f"{status} {t:<22} {passed} passed, {len(bad)} failed  ({time.time() - start:.0f}s)")
        for x in bad or ([] if r.returncode == 0 else lines[-15:]):
            print(f"       {x}")
        if r.returncode:
            failed.append(t)
    print("all tests passed" if not failed else f"{len(failed)} test file(s) failed: {', '.join(failed)}")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
