"""Upgrades of project files on a core update (nogamy/upgrades/).  python nogamy/tests/test_upgrades.py"""
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(sys.argv[1]).resolve() if len(sys.argv) > 1 else Path(__file__).resolve().parents[2]
fails = 0


def check(title, cond, extra=""):
    global fails
    fails += not cond
    print(("PASS " if cond else "FAIL ") + title + (f"  [{extra[-300:]}]" if extra and not cond else ""))


tmp = Path(tempfile.mkdtemp())
core, proj = tmp / "core", tmp / "proj"
ignore = shutil.ignore_patterns(".git", "__pycache__", "_private", "out")
shutil.copytree(ROOT, core, ignore=ignore)
shutil.copytree(ROOT, proj, ignore=ignore)
summary = tmp / "s.md"
sync = [sys.executable, str(core / "nogamy/ops/core_sync.py"), "--core", str(core), "--project", str(proj),
        "--version", "v9", "--summary", str(summary)]

# an old project: platform.md without section 10, and its own notes elsewhere in the file
pf = proj / "_context/platform.md"
text = pf.read_text(encoding="utf-8")
old = text[:text.index("## 10.")].rstrip("\n") + "\n\n<!-- project note: keep me -->\n"
pf.write_text(old, encoding="utf-8")

r = subprocess.run(sync, capture_output=True, text=True, encoding="utf-8")
new = pf.read_text(encoding="utf-8")
check("upgrade: section 10 added to an old platform.md", r.returncode == 0 and "## 10. Platform notes per skill" in new,
      r.stdout + r.stderr)
check("upgrade: the project's own content kept", "<!-- project note: keep me -->" in new)
check("upgrade: listed in the core-update PR summary", "0001_platform_notes_section" in summary.read_text(encoding="utf-8"))

r = subprocess.run(sync, capture_output=True, text=True, encoding="utf-8")
check("upgrade: second run changes nothing", pf.read_text(encoding="utf-8") == new and "upgrades=0" in r.stdout, r.stdout)

# an upgrade that touches a core file is refused, and the update stops
(core / "nogamy/upgrades/0999_bad.py").write_text(
    '"""Bad on purpose."""\nfrom pathlib import Path\n\n\ndef upgrade(project):\n'
    '    Path(project, "AGENTS.md").write_text("x", encoding="utf-8")\n    return ["AGENTS.md: rewritten"]\n',
    encoding="utf-8")
r = subprocess.run(sync, capture_output=True, text=True, encoding="utf-8")
check("upgrade: a core file touched -> the core update stops", r.returncode != 0 and "core file" in r.stderr, r.stderr)
(core / "nogamy/upgrades/0999_bad.py").write_text('"""Crashes."""\n\n\ndef upgrade(project):\n    raise ValueError("boom")\n',
                                                  encoding="utf-8")
r = subprocess.run(sync, capture_output=True, text=True, encoding="utf-8")
check("upgrade: a crash -> the update stops with its error", r.returncode != 0 and "boom" in r.stderr, r.stderr)

shutil.rmtree(tmp, ignore_errors=True)
print("FAILS:", fails)
sys.exit(1 if fails else 0)
