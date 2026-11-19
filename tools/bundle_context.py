"""Pack the project's instructions and memory into one Markdown file, for a chat tool.

A chat tool (ChatGPT, Claude, Gemini) cannot read the repo. This script writes one file to
upload to the chat or to its project: AGENTS.md, PROJECT.md, _context/, the skills you name (with their
references/<platform>.md when --platform is given), and any spec
folders you add. Output goes to _private/ (ignored by Git).

    python tools/bundle_context.py                                   # AGENTS.md + PROJECT.md + _context/
    python tools/bundle_context.py --skills specs,explore-data       # + those skills (nogamy- prefix optional)
    python tools/bundle_context.py --skills write-sql --platform fabric   # + references/fabric.md
    python tools/bundle_context.py --skills all --add stt/sales sources/crm
    python tools/bundle_context.py --out _private/pack-analyst.md

Never packed: _private/ (received material, internal notes) and anything that is not text.
"""
import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
TEXT = {".md", ".sql", ".json", ".yml", ".yaml", ".py", ".txt", ".csv", ".tmdl", ".xml"}
ALWAYS = ["AGENTS.md", "PROJECT.md", "_context"]


def files_under(rel):
    path = (ROOT / rel).resolve()
    if ROOT not in path.parents and path != ROOT:
        sys.exit(f"refused: {rel} is outside the repo")
    if "_private" in path.relative_to(ROOT).parts:
        sys.exit(f"refused: {rel} is under _private/, which is never packed")
    if not path.exists():
        sys.exit(f"not found: {rel}")
    found = [path] if path.is_file() else sorted(p for p in path.rglob("*") if p.is_file())
    return [p for p in found if p.suffix.lower() in TEXT]


def skill_files(names, platform=None):
    skills = ROOT / ".claude" / "skills"
    if names == ["all"]:
        folders = sorted(p.parent for p in skills.glob("*/SKILL.md"))
    else:
        folders = []
        for name in names:
            folder = next((skills / n for n in (name, f"nogamy-{name}") if (skills / n / "SKILL.md").exists()), None)
            if folder is None:
                sys.exit(f"no such skill: {name}")
            folders.append(folder)
    out = []
    for folder in folders:
        out.append(folder / "SKILL.md")
        ref = folder / "references" / f"{platform}.md"
        if platform and ref.exists():
            out.append(ref)
    return out


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--skills", default="", help="comma-separated skill names, or 'all'")
    ap.add_argument("--platform", default=None, help="also pack references/<platform>.md of each skill, e.g. fabric")
    ap.add_argument("--add", nargs="*", default=[], help="extra files or folders, from the repo root")
    ap.add_argument("--out", default="_private/chat-pack.md")
    args = ap.parse_args()

    paths = []
    for rel in ALWAYS + args.add:
        paths += files_under(rel)
    paths += skill_files([s.strip() for s in args.skills.split(",") if s.strip()], args.platform)
    paths = list(dict.fromkeys(paths))  # keep order, drop repeats

    parts = [
        "# Project pack",
        "",
        "One file holding this project's instructions and memory, for an AI chat tool without repo access.",
        "Start with the section `AGENTS.md`. Each section below is one file of the repo; its heading is the file path.",
        "You cannot run anything here: every command or query you need is handed to the person as a run sheet "
        "(AGENTS.md, level L0).",
        "",
        "## Files in this pack",
        "",
        *[f"- `{p.relative_to(ROOT).as_posix()}`" for p in paths],
    ]
    for p in paths:
        rel = p.relative_to(ROOT).as_posix()
        body = p.read_text(encoding="utf-8-sig").rstrip()
        parts += ["", "---", "", f"<!-- file: {rel} -->", f"## FILE: `{rel}`", "", body]

    out = ROOT / args.out
    out.parent.mkdir(parents=True, exist_ok=True)
    text = "\n".join(parts) + "\n"
    out.write_text(text, encoding="utf-8", newline="\n")
    print(f"wrote {out.relative_to(ROOT).as_posix()}: {len(paths)} files, {len(text):,} characters")


if __name__ == "__main__":
    main()
