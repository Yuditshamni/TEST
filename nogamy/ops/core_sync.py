"""Apply a core version to a project. Run by nogamy/ops/core_update.py (skills nogamy-core-update, nogamy-add-pack).

    python core_sync.py --core <checked-out core> --project <project root> --version v1.4.0 --summary out.md
                        [--add-pack fabric]

What it does:
1. Packs: the project's `Packs:` line in PROJECT.md, plus --add-pack. A project with no Packs line was made
   before packs: every pack with a file already in the project is adopted, so nothing it uses is removed;
   the Packs line is written.
2. Core paths = the NEW manifest (from the core) plus the OLD one (from the project), for the packs above,
   so a file the core removed is removed in the project too.
3. Every core path in the project is replaced by the core's copy; core paths the core no longer has are deleted.
   A pack's seeds (`+` lines) are copied only when missing. Nothing outside the manifests is touched.
4. Files of a pack the project does NOT have: removed when identical to the core's copy (they came with the
   template), kept and listed when the project changed them (project work).
5. Runs the core's upgrades (nogamy/upgrades/NNNN_*.py) on the project's own files, in order; each is
   safe twice and lists what it changed. A failing upgrade stops the update.
6. Writes `.core-version`, the read-only globs in `.vscode/settings.json`, and a Markdown summary for the PR.
Standard library only.
"""
import argparse
import filecmp
import importlib.util
import json
import os
import shutil
import stat
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from manifest import MANIFEST, Manifest, pack_defs, project_packs, set_project_packs  # noqa: E402

FRAMEWORK_PREFIX = "fabric/data/"


def choose_packs(core, proj, add):
    """(installed packs, adopted packs, whether the Packs line must be written)."""
    defs = pack_defs(core)
    listed = project_packs(proj)
    adopted = set()
    if listed is None:  # made before packs: keep what it already has
        files = _all_files(proj)
        adopted = {n for n, r in defs.items() if any(r.matches(f) for f in files)}
        listed = set(adopted)
    unknown = set(add) - set(defs)
    if unknown:
        raise SystemExit(f"no such pack in core: {', '.join(sorted(unknown))} (nogamy/packs/)")
    packs = (listed | set(add)) & set(defs)
    return packs, adopted, packs != project_packs(proj)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--core", required=True)
    ap.add_argument("--project", required=True)
    ap.add_argument("--version", required=True)
    ap.add_argument("--summary", required=True)
    ap.add_argument("--add-pack", action="append", default=[])
    a = ap.parse_args()
    core, proj = Path(a.core), Path(a.project)

    packs, adopted, write_line = choose_packs(core, proj, a.add_pack)
    new_m = Manifest.load(core, installed=packs)
    old_m = Manifest.load(proj, installed=packs, packs_from=core) if (proj / MANIFEST).exists() else new_m

    core_files = set(new_m.core_files(core))
    proj_files = _all_files(proj)
    proj_core = {f for f in proj_files if (old_m.is_core(f) or new_m.is_core(f))}

    added = sorted(core_files - proj_core)
    removed = sorted(proj_core - core_files)
    src = lambda f: new_m.source(core, f)  # noqa: E731  (a pack file: its stored copy in nogamy/packs/<name>/)
    changed = sorted(f for f in core_files & proj_core if not filecmp.cmp(src(f), proj / f, shallow=False))

    for f in removed:
        (proj / f).unlink()
    for f in added + changed:
        dst = proj / f
        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(src(f), dst)

    seeded = []
    for f in new_m.seeds():
        if not (proj / f).exists() and src(f).is_file():
            (proj / f).parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(src(f), proj / f)
            seeded.append(f)

    # Files of packs this project does not have: template copies go, project edits stay.
    all_m = Manifest.load(core, installed="all")
    kept = []
    for f in proj_files:
        pack = all_m.pack_of(f)
        if not pack or pack in packs or not (proj / f).exists():
            continue
        if all_m.source(core, f).is_file() and filecmp.cmp(all_m.source(core, f), proj / f, shallow=False):
            (proj / f).unlink()
            removed.append(f)
        else:
            kept.append(f)
    for f in proj_files:  # seeds of packs not installed, untouched since the template
        if all_m.is_seed(f) and all_m.pack_of_seed(f) not in packs and all_m.source(core, f).is_file() \
                and (proj / f).exists() and filecmp.cmp(all_m.source(core, f), proj / f, shallow=False):
            (proj / f).unlink()
            removed.append(f)

    # Core-only paths: a file, or a folder glob ending with "/" (e.g. the stored pack copies nogamy/packs/*/).
    core_only = [x.strip() for x in (core / "nogamy/core-only.txt").read_text(encoding="utf-8").splitlines()
                 if x.strip() and not x.startswith("#")] if (core / "nogamy/core-only.txt").exists() else []
    for entry in core_only:
        if entry.endswith("/"):
            for d in sorted(proj.glob(entry.rstrip("/"))):
                if d.is_dir():
                    removed += [f.relative_to(proj).as_posix() for f in d.rglob("*") if f.is_file()]
                    _rmtree(d)
        elif (proj / entry).is_file():
            (proj / entry).unlink()
            removed.append(entry)
    _prune_empty_dirs(proj, removed)

    upgraded = run_upgrades(core, proj, set(new_m.core_files(core)))

    if write_line:
        set_project_packs(proj, packs)
    (proj / ".core-version").write_text(a.version + "\n", encoding="utf-8")
    write_vscode_settings(proj, Manifest.load(proj, installed=packs))

    framework = [f for f in added + changed + removed if f.startswith(FRAMEWORK_PREFIX)]
    lines = [f"Core `{a.version}` for this project. Packs: {', '.join(sorted(packs)) or 'none'}.", ""]
    if adopted:
        lines += [f"This project was made before packs and already has these files, so it keeps the "
                  f"pack(s) {', '.join(f'`{p}`' for p in sorted(adopted))} (`Packs:` written in `PROJECT.md`).", ""]
    if a.add_pack:
        lines += [f"Pack added: {', '.join(f'`{p}`' for p in a.add_pack)} (`nogamy-add-pack`).", ""]
    for title, items in (("Added", added), ("Changed", changed), ("Removed", sorted(removed)),
                         ("Starting files (project-owned from now on)", seeded)):
        if title.startswith("Starting") and not items:
            continue
        lines.append(f"**{title}** ({len(items)})")
        lines += [f"- `{f}`" for f in items] or ["- none"]
        lines.append("")
    if upgraded:
        lines += ["**Project files adapted to this core** (review these: they are yours)"]
        lines += [f"- {u}" for u in upgraded] + [""]
    if kept:
        lines += ["**Kept, not core here** (a pack this project does not have; the project changed them):"]
        lines += [f"- `{f}`" for f in kept] + [""]
    if framework:
        lines += [
            "> [!WARNING]",
            "> Framework objects changed. Add a numbered migration in `scripts/migrations/` before",
            "> this reaches TEST (`nogamy-deploy`). Files: " + ", ".join(f"`{f}`" for f in framework),
            "",
        ]
    lines += [
        "A `Changed` file that was edited inside this project is overwritten here on purpose: core files",
        "are read-only in projects. If that edit mattered, send it as `nogamy-feedback`.",
    ]
    Path(a.summary).write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"packs={','.join(sorted(packs)) or 'none'} adopted={','.join(sorted(adopted)) or '-'} "
          f"added={len(added)} changed={len(changed)} removed={len(removed)} seeded={len(seeded)} "
          f"kept={len(kept)} framework={len(framework)} upgrades={len(upgraded)}")


def run_upgrades(core, proj, core_paths):
    """Every nogamy/upgrades/NNNN_*.py of the core, in order, on the project. Lines of what changed."""
    out = []
    for f in sorted(Path(core, "nogamy/upgrades").glob("[0-9][0-9][0-9][0-9]_*.py")):
        spec = importlib.util.spec_from_file_location(f"nogamy_upgrade_{f.stem}", f)
        mod = importlib.util.module_from_spec(spec)
        try:
            spec.loader.exec_module(mod)
            changes = list(mod.upgrade(Path(proj)) or [])
        except Exception as ex:  # noqa: BLE001
            raise SystemExit(f"upgrade {f.name} failed: {type(ex).__name__}: {ex}. The core update stops here.")
        for c in changes:
            path = c.split(":", 1)[0].strip()
            if path in core_paths:
                raise SystemExit(f"upgrade {f.name} changed a core file ({path}); upgrades touch project files only.")
            out.append(f"`{f.stem}`: {c}")
    return out


def write_vscode_settings(root, m):
    """Project's `.vscode/settings.json` (project-owned, not core): keep its keys, set the read-only list
    from the manifest and turn on chat.useClaudeHooks (Copilot runs the Nogamy hook from .claude/settings.json)."""
    path = Path(root, ".vscode/settings.json")
    data = json.loads(path.read_text(encoding="utf-8")) if path.exists() else {}
    inc, exc = m.readonly_globs()
    data["files.readonlyInclude"] = inc
    data["files.readonlyExclude"] = exc
    data["chat.useClaudeHooks"] = True
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def _all_files(root):
    root = Path(root)
    return [f.relative_to(root).as_posix() for f in root.rglob("*")
            if f.is_file() and not {".git", "__pycache__"} & set(f.relative_to(root).parts)]


def _rmtree(d):
    """Remove a folder tree, also when Windows (OneDrive) marks files or folders read-only."""
    for dirpath, dirnames, filenames in os.walk(d, topdown=False):
        for name in filenames:
            p = os.path.join(dirpath, name)
            os.chmod(p, stat.S_IWRITE)
            os.unlink(p)
        for name in dirnames:
            p = os.path.join(dirpath, name)
            os.chmod(p, stat.S_IWRITE)
            os.rmdir(p)
    os.chmod(d, stat.S_IWRITE)
    os.rmdir(d)


def _prune_empty_dirs(root, removed):
    for f in removed:
        d = (Path(root) / f).parent
        while d != Path(root) and d.exists() and not any(d.iterdir()):
            os.chmod(d, stat.S_IWRITE)  # Windows / OneDrive may mark the folder read-only
            d.rmdir()
            d = d.parent


if __name__ == "__main__":
    main()
