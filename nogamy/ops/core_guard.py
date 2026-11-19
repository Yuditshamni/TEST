"""PR check in a project: every core file must be exactly the released core. Standard library only.

    python core_guard.py --root <repo> [--base-ref origin/main]

Compares each core file with nogamy/core-checksums.txt (written by the core release).
- A normal PR that edits a core file fails.
- A core-update PR (skill nogamy-core-update) passes: it brings the files and their checksums together.
No exemption by author or branch is needed, so no GitHub App and no special token.
The workflow runs the BASE branch's copy of this script, so a PR cannot weaken the check.
--base-ref: a PR may add a pack to PROJECT.md `Packs:`, never remove one (that would unlock its files).
"""
import argparse
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import checksums  # noqa: E402
from manifest import parse_packs, project_packs  # noqa: E402


def removed_packs(root, base_ref):
    r = subprocess.run(["git", "show", f"{base_ref}:PROJECT.md"], cwd=root, capture_output=True, text=True,
                       encoding="utf-8")
    before = parse_packs(r.stdout) if r.returncode == 0 else None
    return sorted((before or set()) - (project_packs(root) or set()))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", default=".")
    ap.add_argument("--base-ref")
    a = ap.parse_args()
    root = Path(a.root).resolve()
    problems = checksums.verify(root)
    if a.base_ref:
        problems += [f"pack removed from PROJECT.md Packs: {p} (a pack is core; ask the core team)"
                     for p in removed_packs(root, a.base_ref)]
    if not problems:
        print("ok: every core file is the released core")
        return 0
    report(problems, a.base_ref or "origin/main")
    return 1


FIX = {
    "changed core file": "put it back: `git checkout {base} -- {f}`",
    "missing core file": "put it back: `git checkout {base} -- {f}`",
    "new file inside a core path": "move it to a project place (`tools/project/`, a `<project-id>-` skill), or delete it",
}

WHERE = """\
Where a project change goes instead:
- facts, names, environments, rules: `PROJECT.md`, `_context/`
- a platform fact for one skill: `_context/platform.md` §10
- a project skill: `.claude/skills/<project-id>-<what>/` (skill nogamy-create-skill)
- a project script: `tools/project/`
- the core itself is wrong or missing something: tell the agent "feedback: <what and why>"
  (skill nogamy-feedback). The fix comes back to every project in a core update."""


def report(problems, base):
    """Plain lines in the log, an annotation per file on the PR, and a summary on the run page."""
    if problems[0].startswith(checksums.CHECKSUMS):
        lines = [
            "### nogamy-core-guard: this project has no released core yet",
            "",
            f"`{checksums.CHECKSUMS}` is missing, so there is nothing to compare with.",
            "Fix: tell the agent \"core update\" (skill nogamy-core-update). It opens a PR that brings the",
            "core and its checksums; merge it, then re-run this check. Do not create the file by hand.",
        ]
        _out(lines, [(None, problems[0])])
        return
    lines = ["### nogamy-core-guard: this PR changes core files",
             "",
             "Core files come from the Nogamy core and are read-only in a project.",
             "Nothing is lost: undo these, keep the rest of the PR.",
             "",
             "| File | Problem | Fix |",
             "|---|---|---|"]
    notes = []
    for p in problems:
        kind, _, f = p.partition(": ")
        fix = FIX.get(kind)
        if fix:
            lines.append(f"| `{f}` | {kind} | {fix.format(base=base, f=f)} |")
            notes.append((f, f"{kind}. {fix.format(base=base, f=f).replace('`', '')}"))
        else:
            lines.append(f"| | {p} | |")
            notes.append((None, p))
    lines += ["", WHERE]
    _out(lines, notes)


def _out(lines, notes):
    import os
    print("\n".join(lines))
    if os.environ.get("GITHUB_ACTIONS") == "true":
        for f, msg in notes:
            where = f" file={f}" if f else ""
            print(f"::error{where},title=nogamy-core-guard::{msg}")
        summary = os.environ.get("GITHUB_STEP_SUMMARY")
        if summary:
            with open(summary, "a", encoding="utf-8") as s:
                s.write("\n".join(lines) + "\n")


if __name__ == "__main__":
    sys.exit(main())
