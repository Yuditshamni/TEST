"""The daily core update, run by the agent through the skill nogamy-core-update. Standard library + gh.

    python nogamy/ops/core_update.py check  [--force]    once a day: is there a newer core? (+ upload usage)
    python nogamy/ops/core_update.py apply  --version vX  branch, sync, commit, push, open the PR
    python nogamy/ops/core_update.py decline --version vX  not now (asked again tomorrow)
    python nogamy/ops/core_update.py add-pack --name fabric [--set "DEV workspace=X"]... [--open-question "..."]...
                                     the pack from this project's core version, as a PR (skill nogamy-add-pack)
    python nogamy/ops/core_update.py pack-decline --name fabric   not now (the hook asks again in 7 days)

Runs with the developer's own GitHub access (`gh auth`): a Nogamy employee can read the core repo
and can push a branch in the project. No GitHub App, no token in the repo, nothing for the client to approve.
The developer merges the PR; the agent never merges (AGENTS.md).
"""
import argparse
import json
import os
import re
import subprocess
import sys
import tempfile
from datetime import date
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
sys.path.insert(0, str(ROOT / "nogamy" / "hooks"))
import nogamy_telemetry as tel  # noqa: E402

STATE = tel.HOME / "state.json"


def run(*cmd, cwd=ROOT, check=True):
    r = subprocess.run(list(cmd), cwd=cwd, capture_output=True, text=True, encoding="utf-8")
    if check and r.returncode != 0:
        raise SystemExit(f"failed: {' '.join(cmd)}\n{r.stderr.strip()}")
    return r.stdout.strip()


def core_repo():
    repo = os.environ.get("NOGAMY_CORE_REPO") or json.loads((ROOT / "nogamy/core.json").read_text(encoding="utf-8"))["core_repo"]
    if "<" in repo:
        raise SystemExit("nogamy/core.json has no core repo yet (nogamy/docs/setup.md, step 1).")
    return repo


def state():
    try:
        return json.loads(STATE.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return {}


def save_state(s):
    tel.HOME.mkdir(parents=True, exist_ok=True)
    STATE.write_text(json.dumps(s, indent=2), encoding="utf-8")


def key():
    return str(ROOT).lower()


def current_version():
    f = ROOT / ".core-version"
    return f.read_text(encoding="utf-8").strip() if f.exists() else "none"


def check(force):
    s = state()
    mine = s.get(key(), {})
    today = date.today().isoformat()
    if mine.get("checked") == today and not force:
        print(json.dumps({"checked_today": True, "current": current_version()}))
        return
    rel = json.loads(run("gh", "release", "view", "--repo", core_repo(), "--json", "tagName,body,publishedAt"))
    latest, cur = rel["tagName"], current_version()
    declined_today = mine.get("declined") == latest and mine.get("declined_on") == today
    out = {"current": cur, "latest": latest, "update_available": latest != cur and not declined_today,
           "published": rel.get("publishedAt"), "notes": rel.get("body", "")[:4000]}
    mine["checked"] = today
    s[key()] = mine
    save_state(s)
    tel.emit("core_update_checked", None, latest=latest, update_available=out["update_available"])
    try:
        import usage_upload
        out["usage_uploaded"] = usage_upload.upload(core_repo())
    except Exception as ex:  # usage upload never blocks the update
        out["usage_uploaded"] = f"skipped: {str(ex)[:120]}"
    print(json.dumps(out, ensure_ascii=False, indent=2))


def default_branch():
    ref = run("git", "symbolic-ref", "--short", "refs/remotes/origin/HEAD", check=False)
    return ref.split("/", 1)[1] if "/" in ref else "main"


def apply(version):
    url, branch = sync_pr(version, f"nogamy/core-update-{version}", f"core update {version}",
                          f"core: update to {version} — Nogamy core release", [], "nogamy-core-update")
    tel.emit("core_update_applied", None, version=version)
    print(json.dumps({"pr": url, "branch": branch}))


def add_pack(name, sets, questions):
    version = current_version()
    if version == "none":
        raise SystemExit("No .core-version: run the core update first (nogamy-core-update), then add the pack.")

    def edit_project():
        set_values(ROOT / "PROJECT.md", sets)
        if questions:
            f = ROOT / "_context/open-questions.md"
            text = f.read_text(encoding="utf-8") if f.exists() else "# Open questions\n"
            f.parent.mkdir(parents=True, exist_ok=True)
            added = "".join(f"- {q} (pack `{name}`)\n" for q in questions)
            f.write_text(text.rstrip("\n") + "\n" + added, encoding="utf-8")

    url, branch = sync_pr(version, f"nogamy/add-pack-{name}", f"add pack {name}",
                          f"core: add pack {name} — the project works on this platform", ["--add-pack", name],
                          "nogamy-add-pack", after_sync=edit_project)
    tel.emit("pack_added", None, pack=name, version=version)
    print(json.dumps({"pr": url, "branch": branch}))


def set_values(path, sets):
    """`--set "DEV workspace=X"` → the line `- DEV workspace: X` in PROJECT.md. Only a line that exists;
    the text after the placeholder (a comment) is kept."""
    if not sets or not path.exists():
        return
    text = path.read_text(encoding="utf-8")
    for kv in sets:
        if "=" not in kv:
            raise SystemExit(f"--set needs KEY=VALUE: {kv}")
        k, v = (x.strip() for x in kv.split("=", 1))
        pat = re.compile(r"^([ \t]*[-*][ \t]*" + re.escape(k) + r":[ \t]*)(<[^>\n]*>|[^ \t\n]*)(.*)$", re.M | re.I)
        if not pat.search(text):
            raise SystemExit(f"PROJECT.md has no line '- {k}:'")
        text = pat.sub(lambda m: m.group(1) + v + m.group(3), text, count=1)
    path.write_text(text, encoding="utf-8")


def sync_pr(version, branch, title, message, sync_args, label, after_sync=None):
    """Branch from the default branch, run the core's core_sync at `version`, commit, push, open the PR.
    Always returns to the starting branch."""
    if run("git", "status", "--porcelain"):
        raise SystemExit("The working tree has uncommitted changes. Commit or stash them first, then run again.")
    start = run("git", "rev-parse", "--abbrev-ref", "HEAD")
    base = default_branch()
    run("git", "fetch", "origin", base)
    run("git", "switch", "-c", branch, f"origin/{base}")
    update = label == "nogamy-core-update"
    try:
        with tempfile.TemporaryDirectory() as tmp:
            src = Path(tmp) / "core"
            run("gh", "repo", "clone", core_repo(), str(src), "--", "--depth", "1", "--branch", version, "--quiet")
            summary = Path(tmp) / "summary.md"
            print(run(sys.executable, str(src / "nogamy/ops/core_sync.py"), "--core", str(src), "--project", str(ROOT),
                      "--version", version, "--summary", str(summary), *sync_args))
            if after_sync:
                after_sync()
            if update:
                notes = run("gh", "release", "view", version, "--repo", core_repo(), "--json", "body", "-q", ".body",
                            check=False)
                head = f"## Core update {current_version_from_git(base)} → {version}\n\n{notes}"
            else:
                head = f"## {title} (core {version})"
            body = Path(tmp) / "body.md"
            body.write_text(f"{head}\n\n## Files\n\n{summary.read_text(encoding='utf-8')}\n\n"
                            f"Opened by `{label}`. Review and merge it yourself.\n", encoding="utf-8")
            run("git", "add", "-A")
            run("git", "commit", "-m", message)
            run("git", "push", "-u", "origin", branch)
            url = run("gh", "pr", "create", "--base", base, "--head", branch, "--title", title,
                      "--body-file", str(body), "--label", label, check=False)
            if not url.startswith("http"):
                url = run("gh", "pr", "create", "--base", base, "--head", branch, "--title", title,
                          "--body-file", str(body))
    finally:
        run("git", "switch", start, check=False)
    return url, branch


def current_version_from_git(base):
    return run("git", "show", f"origin/{base}:.core-version", check=False) or "none"


def decline(version):
    s = state()
    mine = s.get(key(), {})
    mine.update(declined=version, declined_on=date.today().isoformat())
    s[key()] = mine
    save_state(s)
    tel.emit("core_update_declined", None, version=version)
    print(json.dumps({"declined": version, "ask_again": "tomorrow"}))


def pack_decline(name):
    s = state()
    mine = s.get(key(), {})
    mine.setdefault("pack_declined", {})[name] = date.today().isoformat()
    s[key()] = mine
    save_state(s)
    tel.emit("pack_declined", None, pack=name)
    print(json.dumps({"declined": name, "ask_again": "in 7 days"}))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("cmd", choices=["check", "apply", "decline", "add-pack", "pack-decline"])
    ap.add_argument("--version")
    ap.add_argument("--name")
    ap.add_argument("--set", action="append", default=[])
    ap.add_argument("--open-question", action="append", default=[])
    ap.add_argument("--force", action="store_true")
    a = ap.parse_args()
    if a.cmd in ("add-pack", "pack-decline"):
        if not a.name:
            raise SystemExit("--name is required")
        if a.cmd == "add-pack":
            add_pack(a.name, a.set, a.open_question)
        else:
            pack_decline(a.name)
    elif a.cmd == "check":
        check(a.force)
    elif not a.version:
        raise SystemExit("--version is required")
    elif a.cmd == "apply":
        apply(a.version)
    else:
        decline(a.version)


if __name__ == "__main__":
    main()
