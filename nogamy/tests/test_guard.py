"""End to end, offline: release -> "Use this template" -> a core edit is caught -> undone -> a newer core
reaches the project by a core update and passes the guard.  python nogamy/tests/test_guard.py"""
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(sys.argv[1]).resolve() if len(sys.argv) > 1 else Path(__file__).resolve().parents[2]
PY = sys.executable
fails = 0


def check(title, cond, extra=""):
    global fails
    fails += not cond
    print(("PASS " if cond else "FAIL ") + title + (f"  [{extra[-300:]}]" if extra and not cond else ""))


def run(args, cwd):
    env = {k: v for k, v in os.environ.items() if not k.startswith("GITHUB_")}
    return subprocess.run(args, cwd=cwd, capture_output=True, text=True, encoding="utf-8", env=env)


def git(cwd, *args):
    return run(["git", "-c", "user.email=nogamy-test", "-c", "user.name=test", *args], cwd)


tmp = Path(tempfile.mkdtemp())
core, proj = tmp / "core", tmp / "proj"
ignore = shutil.ignore_patterns(".git", "__pycache__", "_private", "out")
shutil.copytree(ROOT, core, ignore=ignore)

# 1. release v1: checksums written into the core
r = run([PY, "nogamy/ops/checksums.py", "write", "v1"], core)
check("release v1: checksums written", r.returncode == 0 and (core / "nogamy/core-checksums.txt").exists(), r.stderr)

# 2. "Use this template", then the project's first core update (removes core-only files)
shutil.copytree(core, proj, ignore=ignore)
sync = [PY, str(core / "nogamy/ops/core_sync.py"), "--core", str(core), "--project", str(proj), "--summary", str(tmp / "s.md")]
r = run(sync + ["--version", "v1"], proj)
check("project: first core update runs", r.returncode == 0, r.stdout + r.stderr)
check("project: core-only release workflow removed", not (proj / ".github/workflows/nogamy-core-release.yml").exists())
git(proj, "init", "-q")
git(proj, "add", "-A")
git(proj, "commit", "-qm", "project start")
git(proj, "update-ref", "refs/remotes/origin/main", "HEAD")
guard = [PY, "nogamy/ops/core_guard.py", "--root", ".", "--base-ref", "origin/main"]

r = run(guard, proj)
check("guard: a fresh project passes", r.returncode == 0, r.stdout)

# 3. a developer edits a core skill and adds a script under tools/
skill = proj / ".claude/skills/nogamy-naming/SKILL.md"
skill.write_text(skill.read_text(encoding="utf-8") + "\nlocal change\n", encoding="utf-8")
(proj / "tools/my_script.py").write_text("print(1)\n", encoding="utf-8")
r = run(guard, proj)
check("guard: an edited core skill fails the PR", r.returncode == 1 and "changed core file" in r.stdout, r.stdout)
check("guard: says the exact command to undo it",
      "git checkout origin/main -- .claude/skills/nogamy-naming/SKILL.md" in r.stdout, r.stdout)
check("guard: a new file in tools/ is named, with where it belongs",
      "tools/my_script.py" in r.stdout and "tools/project/" in r.stdout, r.stdout)
check("guard: points to feedback for a core change", "feedback:" in r.stdout, r.stdout)

# 4. the developer follows the message
git(proj, "checkout", "origin/main", "--", ".claude/skills/nogamy-naming/SKILL.md")
(proj / "tools/my_script.py").unlink()
r = run(guard, proj)
check("guard: after the printed fix, passes again", r.returncode == 0, r.stdout)

# 5. the core team improves a skill and releases v2; the project's core update brings it
cskill = core / ".claude/skills/nogamy-naming/SKILL.md"
cskill.write_text(cskill.read_text(encoding="utf-8") + "\nimproved in v2\n", encoding="utf-8")
run([PY, "nogamy/ops/checksums.py", "write", "v2"], core)
r = run(sync + ["--version", "v2"], proj)
check("core update v2: runs", r.returncode == 0, r.stdout + r.stderr)
check("core update v2: the improved skill reached the project", "improved in v2" in skill.read_text(encoding="utf-8"))
check("core update v2: .core-version is v2", (proj / ".core-version").read_text(encoding="utf-8").strip() == "v2")
r = run(guard, proj)
check("guard: the core-update PR passes (files and checksums together)", r.returncode == 0, r.stdout)

# 6. a project without released checksums gets the core-update message, not "revert"
(proj / "nogamy/core-checksums.txt").unlink()
r = run(guard, proj)
check("guard: no checksums -> tells to run a core update", r.returncode == 1 and "core update" in r.stdout, r.stdout)

shutil.rmtree(tmp, ignore_errors=True)
print("FAILS:", fails)
sys.exit(1 if fails else 0)
