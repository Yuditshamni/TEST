"""End-to-end: a project made with "Use this template", then a core update (no pack), then add-pack fabric."""
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

core = Path(sys.argv[1]).resolve() if len(sys.argv) > 1 else Path(__file__).resolve().parents[2]
proj = Path(tempfile.mkdtemp()) / "proj"
shutil.copytree(core, proj, ignore=shutil.ignore_patterns(".git", "__pycache__", "_private"))
# what "Use this template" leaves: the template's files; a project fills PROJECT.md (Packs: none)
sync = [sys.executable, str(core / "nogamy/ops/core_sync.py"), "--core", str(core), "--project", str(proj),
        "--version", "v0.1.0", "--summary", str(proj.parent / "s.md")]


def has(p):
    return (proj / p).exists()


def check(title, cond):
    print(("PASS " if cond else "FAIL ") + title)
    return 0 if cond else 1


fails = 0
print("before:", "stored copy" if has("nogamy/packs/fabric") else "-", "| root fabric/:", has("fabric"))
r = subprocess.run(sync, capture_output=True, text=True)
print("sync 1:", r.stdout.strip() or r.stderr.strip()[-400:])
fails += check("no-pack project: no fabric/ at root", not has("fabric"))
fails += check("no-pack project: no tools/fabric", not has("tools/fabric"))
fails += check("no-pack project: stored copies removed (nogamy/packs/fabric/)", not has("nogamy/packs/fabric"))
fails += check("no-pack project: pack list kept (nogamy/packs/fabric.txt)", has("nogamy/packs/fabric.txt"))
fails += check("no-pack project: skills still there", has(".claude/skills/nogamy-write-sql/references/fabric.md"))

r = subprocess.run(sync + ["--add-pack", "fabric"], capture_output=True, text=True)
print("sync 2:", r.stdout.strip() or r.stderr.strip()[-400:])
fails += check("fabric project: SP_DQA at its project path",
               has("fabric/data/WH_DWH.Warehouse/QA/StoredProcedures/SP_DQA.sql"))
fails += check("fabric project: tools/fabric/wh_sql.py", has("tools/fabric/wh_sql.py"))
fails += check("fabric project: tools/migrate/run_migrations.py", has("tools/migrate/run_migrations.py"))
fails += check("fabric project: .mcp.json", has(".mcp.json"))
fails += check("fabric project: no stored copy left", not has("nogamy/packs/fabric"))
fails += check("fabric project: PROJECT.md says Packs: fabric",
               "Packs: fabric" in (proj / "PROJECT.md").read_text(encoding="utf-8"))

sys.path.insert(0, str(core / "nogamy/ops"))
from checksums import write  # noqa: E402
n = write(core, "test")  # release checksums, from the core
shutil.copyfile(core / "nogamy/core-checksums.txt", proj / "nogamy/core-checksums.txt")
(core / "nogamy/core-checksums.txt").unlink()
r = subprocess.run([sys.executable, str(proj / "nogamy/ops/checksums.py"), "verify"], capture_output=True, text=True)
print("checksums:", n, "files in the release;", r.stdout.strip().splitlines()[-1])
fails += check("fabric project: every core file (pack included) matches the release", r.returncode == 0)
print("FAILS:", fails)
shutil.rmtree(proj.parent, ignore_errors=True)
sys.exit(1 if fails else 0)
