"""SHA-256 of every core file, written at release, checked in every project PR. Standard library only.

    python nogamy/ops/checksums.py write     (core release) -> nogamy/core-checksums.txt
    python nogamy/ops/checksums.py verify    (project PR)   -> exit 1 if a core file differs

Line endings are normalized (CRLF -> LF) before hashing, so a Windows checkout does not count as a change.
The checksums file does not list itself.
The release lists every pack's files too; a project checks only the core of its own packs (PROJECT.md `Packs:`).
"""
import hashlib
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from manifest import Manifest  # noqa: E402

ROOT = Path(__file__).resolve().parents[2]
CHECKSUMS = "nogamy/core-checksums.txt"


def digest(path):
    data = Path(path).read_bytes()
    if b"\0" not in data[:8000]:
        data = data.replace(b"\r\n", b"\n")
    return hashlib.sha256(data).hexdigest()


def current(root=ROOT, installed=None):
    m = Manifest.load(root, installed=installed)
    return {f: digest(m.source(root, f)) for f in m.core_files(root) if f != CHECKSUMS}


def read(root=ROOT):
    p = Path(root) / CHECKSUMS
    if not p.exists():
        return None
    out = {}
    for line in p.read_text(encoding="utf-8").splitlines():
        if line.strip() and not line.startswith("#"):
            h, f = line.split(None, 1)
            out[f.strip()] = h
    return out


def write(root=ROOT, version=""):
    sums = current(root, installed="all")
    lines = [f"# Nogamy core {version}: SHA-256 of every core file (nogamy/ops/checksums.py). Do not edit."]
    lines += [f"{h}  {f}" for f, h in sorted(sums.items())]
    (Path(root) / CHECKSUMS).write_text("\n".join(lines) + "\n", encoding="utf-8")
    return len(sums)


def verify(root=ROOT):
    """List of problems; empty = every core file is exactly the released one."""
    expected = read(root)
    if expected is None:
        return [f"{CHECKSUMS} is missing: the core was not installed by a core update"]
    m = Manifest.load(root)
    expected = {f: h for f, h in expected.items() if m.is_core(f)}
    actual = current(root)
    problems = []
    for f, h in sorted(expected.items()):
        if f not in actual:
            problems.append(f"missing core file: {f}")
        elif actual[f] != h:
            problems.append(f"changed core file: {f}")
    for f in sorted(set(actual) - set(expected)):
        problems.append(f"new file inside a core path: {f}")
    return problems


if __name__ == "__main__":
    cmd = sys.argv[1] if len(sys.argv) > 1 else "verify"
    if cmd == "write":
        print(f"{write(ROOT, sys.argv[2] if len(sys.argv) > 2 else '')} files")
        sys.exit(0)
    probs = verify(ROOT)
    for p in probs:
        print(p)
    print("ok" if not probs else f"{len(probs)} problems")
    sys.exit(1 if probs else 0)
