"""Read nogamy/core-manifest.txt and the packs in nogamy/packs/, and tell whether a repo path is core.

Used by core_sync.py, core_guard.py, checksums.py, validate_core.py and the agent hook. Standard library only.

A pack (nogamy/packs/<name>.txt, same syntax as the manifest) is the part of the core for one platform,
e.g. fabric. Its paths are core only in a project that installed it (PROJECT.md: `Packs: fabric`).
In a project without it they are not core, whatever core-manifest.txt says: the pack owns them.
A pack line starting with `+` is a seed: copied once when missing, then a project file (never core).

Where a pack's files live: in the core repo, under nogamy/packs/<name>/ at their project path
(nogamy/packs/fabric/tools/fabric/wh_sql.py → tools/fabric/wh_sql.py), so the template root holds no
platform files. In a project that added the pack, at the project path itself. `source()` gives the
file to read for a project path; `core_files()` lists project paths in both cases.
The stored copies under nogamy/packs/<name>/ are never core in a project (core-only.txt removes them).
"""
import os
import re
from fnmatch import fnmatchcase
from pathlib import Path

MANIFEST = "nogamy/core-manifest.txt"
PACKS_DIR = "nogamy/packs"
ALL = "all"

# What tells that a project works on a pack's platform (the hook offers the pack; core_sync adopts it).
SIGNALS = {
    "fabric": {
        "platform": ("fabric",),
        "dirs": ("*.Warehouse", "*.Lakehouse", "*.DataPipeline", "*.SemanticModel", "*.Notebook"),
        "words": ("fabric", "lakehouse", "onelake", "warehouse", "data factory", "פבריק"),
    },
}
SKIP_DIRS = {".git", "node_modules", "_private", "__pycache__", ".venv", "venv"}


def norm(path):
    p = str(path).replace("\\", "/")
    while p.startswith("./"):
        p = p[2:]
    return p.lstrip("/")


def _match(entry, path):
    e_parts = entry.rstrip("/").split("/")
    p_parts = path.split("/")
    if entry.endswith("/"):  # folder: path must be inside it
        if len(p_parts) <= len(e_parts):
            return False
    elif len(p_parts) != len(e_parts):
        return False
    return all(fnmatchcase(p, e) for p, e in zip(p_parts, e_parts))


class Rules:
    """One manifest-syntax file: include, `!` exclude, `+` seed."""

    def __init__(self, text):
        self.include, self.exclude, self.seeds = [], [], []
        for raw in text.splitlines():
            line = raw.split("#", 1)[0].strip()
            if not line:
                continue
            if line.startswith("!"):
                self.exclude.append(norm(line[1:].strip()))
            elif line.startswith("+"):
                self.seeds.append(norm(line[1:].strip()))
            else:
                self.include.append(norm(line))

    def matches(self, p):
        return not any(_match(e, p) for e in self.exclude) and any(_match(e, p) for e in self.include)


def stored_pack_path(path):
    """(pack name, project path) for a file stored under nogamy/packs/<name>/; else None."""
    p = norm(path)
    prefix = PACKS_DIR + "/"
    if not p.startswith(prefix):
        return None
    parts = p[len(prefix):].split("/", 1)
    return (parts[0], parts[1]) if len(parts) == 2 and parts[1] else None


def pack_defs(root):
    d = Path(root, PACKS_DIR)
    return {f.stem: Rules(f.read_text(encoding="utf-8")) for f in sorted(d.glob("*.txt"))} if d.is_dir() else {}


def project_packs(root):
    """Packs named in PROJECT.md (`Packs: fabric, sqlserver`), a set; None when there is no Packs line."""
    try:
        return parse_packs(Path(root, "PROJECT.md").read_text(encoding="utf-8"))
    except OSError:
        return None


def parse_packs(project_md_text):
    m = re.search(r"^[ \t]*[-*]?[ \t]*Packs:[ \t]*(.*)$", project_md_text, re.M)
    if not m:
        return None
    value = re.sub(r"<[^>]*>|\([^)]*\)|`", " ", m.group(1))
    return {w.lower() for w in re.split(r"[\s,]+", value) if w and w.lower() != "none"}


def set_project_packs(root, packs):
    """Write the Packs line in PROJECT.md (after the Telemetry line, or at the end of Identity)."""
    path = Path(root, "PROJECT.md")
    if not path.exists():
        return False
    text = path.read_text(encoding="utf-8")
    line = f"- Packs: {', '.join(sorted(packs)) or 'none'}   (core parts per platform: `nogamy-add-pack`)"
    if re.search(r"^[ \t]*[-*]?[ \t]*Packs:.*$", text, re.M):
        text = re.sub(r"^[ \t]*[-*]?[ \t]*Packs:.*$", line, text, count=1, flags=re.M)
    elif re.search(r"^[ \t]*[-*]?[ \t]*Telemetry:.*$", text, re.M):
        text = re.sub(r"^([ \t]*[-*]?[ \t]*Telemetry:.*)$", lambda m: m.group(1) + "\n" + line, text, count=1, flags=re.M)
    else:
        text = text.rstrip("\n") + "\n" + line + "\n"
    path.write_text(text, encoding="utf-8")
    return True


def platform_signal(root, pack):
    """Why this repo looks like it works on the pack's platform: a short reason, or None.
    PROJECT.md `Platform:` line, then a folder like *.Warehouse (first hit wins; stays fast)."""
    sig = SIGNALS.get(pack)
    if not sig:
        return None
    try:
        text = Path(root, "PROJECT.md").read_text(encoding="utf-8")
        m = re.search(r"^[ \t]*[-*]?[ \t]*Platform:[ \t]*(.*)$", text, re.M)
        value = re.sub(r"<[^>]*>|\([^)]*\)", " ", m.group(1)).strip() if m else ""  # not the skeleton's placeholder
        if value and any(w in value.lower() for w in sig["platform"]):
            return f"PROJECT.md says Platform: {value}"
    except OSError:
        pass
    defs = pack_defs(root)
    for dirpath, dirnames, _ in os.walk(root):
        for d in dirnames:
            if any(fnmatchcase(d, g) for g in sig["dirs"]):
                rel = norm(os.path.relpath(os.path.join(dirpath, d), root))
                if _has_own_file(root, rel, defs):  # not only the template's framework files
                    return f"the repo has {rel}/"
        dirnames[:] = [d for d in dirnames if d not in SKIP_DIRS and not d.startswith(".")]
    return None


def _has_own_file(root, rel_dir, defs):
    for dirpath, _, files in os.walk(Path(root, rel_dir)):
        for f in files:
            p = norm(os.path.relpath(os.path.join(dirpath, f), root))
            if not any(r.matches(p) for r in defs.values()):
                return True
    return False


def prompt_signal(prompt, pack):
    sig = SIGNALS.get(pack)
    p = (prompt or "").lower()
    return next((w for w in (sig or {}).get("words", ()) if re.search(r"(?<![\w])" + re.escape(w) + r"(?![\w])", p)), None)


class Manifest:
    """The core of one repo: core-manifest.txt, plus the installed packs, minus the packs not installed.

    installed: a set of pack names; ALL (every pack: the core repo, release, validator);
    None = read PROJECT.md, and a project with no Packs line (made before packs) has every pack.
    """

    def __init__(self, text, packs=None, installed=ALL):
        self.base = Rules(text)
        self.packs = packs or {}
        self.installed = set(self.packs) if installed == ALL else set(installed) & set(self.packs)
        # kept for callers that read the base lists
        self.include, self.exclude = self.base.include, self.base.exclude

    @classmethod
    def load(cls, root=".", installed=None, packs_from=None):
        """packs_from: where the pack definitions are (default root); core_sync reads them from the new core."""
        if installed is None:
            installed = project_packs(root)
            if installed is None:
                installed = ALL
        return cls(Path(root, MANIFEST).read_text(encoding="utf-8"), pack_defs(packs_from or root), installed)

    _match = staticmethod(_match)

    def pack_of(self, path):
        """The pack that owns this path, or None."""
        p = norm(path)
        return next((n for n, r in self.packs.items() if r.matches(p)), None)

    def pack_of_seed(self, path):
        p = norm(path)
        return next((n for n, r in self.packs.items() for e in r.seeds if _match(e, p) or e == p), None)

    def is_seed(self, path):
        return self.pack_of_seed(path) is not None

    def is_core(self, path):
        p = norm(path)
        if stored_pack_path(p):  # the core's stored copy of a pack file: listed under its project path
            return False
        if self.is_seed(p):
            return False
        pack = self.pack_of(p)
        if pack:
            return pack in self.installed
        return self.base.matches(p)

    def source(self, root, path):
        """The file to read for a project path: the stored copy in nogamy/packs/<pack>/ when there is one."""
        p = norm(path)
        pack = self.pack_of(p) or self.pack_of_seed(p)
        if pack:
            stored = Path(root, PACKS_DIR, pack, p)
            if stored.is_file():
                return stored
        return Path(root, p)

    def core_files(self, root):
        """Every core path here, as a project path (skips .git and __pycache__).
        Stored pack files (nogamy/packs/<name>/...) are listed under their project path."""
        root = Path(root)
        out = set()
        for f in root.rglob("*"):
            parts = f.relative_to(root).parts
            if f.is_file() and ".git" not in parts and "__pycache__" not in parts:
                rel = norm(f.relative_to(root).as_posix())
                stored = stored_pack_path(rel)
                if stored:
                    name, target = stored
                    if name in self.packs and self.pack_of(target) == name and self.is_core(target):
                        out.add(target)
                elif self.is_core(rel):
                    out.add(rel)
        return sorted(out)

    def stored_files(self, root, pack):
        """Project paths of every file the core stores for one pack, seeds included."""
        d = Path(root, PACKS_DIR, pack)
        return sorted(norm(f.relative_to(d).as_posix()) for f in d.rglob("*")
                      if f.is_file() and "__pycache__" not in f.parts) if d.is_dir() else []

    def seeds(self):
        return [e for n in sorted(self.installed) for e in self.packs[n].seeds]

    def readonly_globs(self):
        """Globs for VS Code files.readonlyInclude / readonlyExclude (exclude wins in VS Code)."""
        g = lambda e: (e + "**") if e.endswith("/") else e  # noqa: E731
        inc = {g(e): True for e in self.base.include}
        exc = {g(e): True for e in self.base.exclude}
        for name, r in self.packs.items():
            if name in self.installed:
                inc.update({g(e): True for e in r.include})
                exc.update({g(e): True for e in r.exclude})
            else:
                exc.update({g(e): True for e in r.include})
            exc.update({g(e): True for e in r.seeds})
        return inc, exc
