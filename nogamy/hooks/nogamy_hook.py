"""The one agent hook of a Nogamy repo. Standard library only.

Started by nogamy-hook.sh (finds Python 3 and the repo root) from each tool's config: .claude/settings.json
(Claude Code, and GitHub Copilot in VS Code, which reads it when chat.useClaudeHooks is on — set in
.vscode/settings.json), .codex/hooks.json (Codex), .cursor/hooks.json (Cursor), .gemini/settings.json (Gemini CLI).
No .github/hooks file: Copilot reads both sources and would run the hook twice.
normalize() turns each tool's event into one shape; a bug in this hook never stops the work (exit 0, the PR
check nogamy-core-guard is the net).

    PreToolUse:   1. core lock — a write to a core file (nogamy/core-manifest.txt) is blocked
                  2. skill gate — enforce_skills.decide (skill before file, base_prompt by section)
                  3. usage event — which skill was opened
    SessionStart: usage event session_start; the daily core check; a missing pack (nogamy-add-pack)
    UserPromptSubmit: a missing pack, when the request names its platform (once a day)

A block = exit 2 + reason on stderr (Claude Code, Codex) + {"permissionDecision": "deny"} on stdout
(Copilot). Everything else exits 0 with no output.
In the core repo itself (origin = core_repo in nogamy/core.json) the lock is off: that is where core is edited.
"""
import json
import os
import re
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import enforce_skills  # noqa: E402
import nogamy_telemetry as tel  # noqa: E402

ROOT = HERE.parent.parent
sys.path.insert(0, str(ROOT / "nogamy" / "ops"))

SKILL_PATH = re.compile(r"(?:\.claude|\.github|\.agents)/skills/([\w.-]+)/SKILL\.md", re.I)
SHELL_TOOLS = {"Bash", "PowerShell", "run_in_terminal", "shell", "bash", "powershell"}
LOCK_MSG = ("{path} is a Nogamy core file: read-only in a project (AGENTS.md → Core and project). "
            "Do not edit it and do not work around this block. If the core should change, use the "
            "nogamy-feedback skill: draft the feedback, show it to the developer, send it after they approve.")


def norm(p):
    return (p or "").replace("\\", "/")


def rel(path):
    p = norm(path)
    root = norm(str(ROOT)).rstrip("/") + "/"
    if p.lower().startswith(root.lower()):
        p = p[len(root):]
    while p.startswith("./"):
        p = p[2:]
    return p.strip("'\"")


def in_core_repo():
    """True only in the Nogamy core repo itself: a git remote points to core_repo (nogamy/core.json).
    A new project made with "Use this template" still has the core-only files until its first core update, so
    files are never the test. Unknown (no git, no remote) -> False: the lock stays on."""
    if os.environ.get("NOGAMY_CORE_DEV") == "1":  # a core maintainer working in a copy with another remote
        return True
    try:
        core = json.loads((ROOT / "nogamy" / "core.json").read_text(encoding="utf-8")).get("core_repo", "")
        r = subprocess.run(["git", "-C", str(ROOT), "config", "--get-regexp", r"^remote\..*\.url$"],
                           capture_output=True, text=True, timeout=5)
    except (OSError, ValueError, subprocess.SubprocessError):
        return False
    return bool(core) and "<" not in core and core.lower() in r.stdout.lower()


def manifest():
    try:
        from manifest import Manifest
        return Manifest.load(ROOT)
    except Exception:
        return None


def core_lock(d, m):
    tool = d.get("tool_name") or d.get("toolName")
    i = enforce_skills.tool_args(d)
    if tool in enforce_skills.WRITE_TOOLS or tool in {"NotebookEdit", "replace_string_in_file", "create_file",
                                                       "insert_edit_into_file", "apply_patch"}:
        targets = [i.get("file_path") or i.get("path") or i.get("filePath") or ""]
        targets += [x.get("filePath", "") for x in i.get("edits", []) if isinstance(x, dict)]
        # apply_patch (Codex, Copilot): the paths are inside the patch text
        patch = str(i.get("command") or i.get("input") or i.get("patch") or "")
        targets += re.findall(r"^\*\*\* (?:Update|Add|Delete) File: (.+?)\s*$", patch, re.M)
        for t in targets:
            r = rel(t)
            if r and m.is_core(r):
                return r
    if tool in SHELL_TOOLS:
        cmd = i.get("command") or ""
        cmd = " ".join(cmd) if isinstance(cmd, list) else str(cmd)
        if "*** Begin Patch" in cmd:  # Codex sends apply_patch through the shell tool
            return core_lock({"tool_name": "apply_patch", "tool_input": {"command": cmd}}, m)
        for t in shell_write_targets(norm(cmd)):
            r = rel(t)
            if r and m.is_core(r):
                return r
    return None


WRITE_VERBS_ALL = {"rm", "mv", "tee", "truncate", "remove-item", "set-content", "add-content", "clear-content",
                   "move-item", "rename-item", "new-item", "out-file", "del", "erase"}
WRITE_VERBS_LAST = {"cp", "copy-item", "copy", "install", "rsync"}


def shell_write_targets(cmd):
    """Paths a shell command writes: redirect targets, and arguments of write verbs. Reads are free."""
    targets = re.findall(r"(?<![0-9&])>>?\s*([^\s|;&]+)", cmd)
    for seg in re.split(r"\|\||&&|[|;\n]", cmd):
        words = [w.strip("'\"") for w in seg.split()]
        if not words:
            continue
        verb = words[0].lower()
        args = [w for w in words[1:] if not w.startswith("-")]
        if verb == "sed" and any(w.startswith("-i") for w in words[1:]):
            targets += args[1:]
        elif verb == "git" and args[:1] and args[0] in ("checkout", "restore", "rm", "mv"):
            targets += args[1:]
        elif verb in WRITE_VERBS_ALL:
            targets += args
        elif verb in WRITE_VERBS_LAST and args:
            targets.append(args[-1])
    return targets


def skills_used(d):
    tool = d.get("tool_name") or d.get("toolName") or ""
    i = enforce_skills.tool_args(d)
    if tool.lower() == "skill":
        n = i.get("name") or i.get("skill")
        return [n] if n else []
    if tool in enforce_skills.READ_TOOLS or tool in {"read_file", "view_file"}:
        text = norm(i.get("file_path") or i.get("path") or i.get("filePath") or "")
    elif tool in SHELL_TOOLS:  # cat / Get-Content of a SKILL.md counts as reading it
        text = norm(str(i.get("command") or ""))
    else:  # editing a skill file is not using the skill
        return []
    return sorted(set(SKILL_PATH.findall(text)))


def daily_check_due():
    from datetime import date
    try:
        core = json.loads((ROOT / "nogamy" / "core.json").read_text(encoding="utf-8")).get("core_repo", "<")
        if "<" in core or in_core_repo():
            return False
        s = json.loads((tel.HOME / "state.json").read_text(encoding="utf-8"))
        return s.get(str(ROOT).lower(), {}).get("checked") != date.today().isoformat()
    except (OSError, ValueError):
        return True


def daily_check_message():
    import subprocess
    try:
        r = subprocess.run([sys.executable, str(ROOT / "nogamy/ops/core_update.py"), "check"], cwd=ROOT,
                           capture_output=True, text=True, encoding="utf-8", timeout=8)
        out = json.loads(r.stdout) if r.returncode == 0 else None
    except (OSError, ValueError, subprocess.SubprocessError):
        out = None
    if not out:
        return ("Nogamy: the daily core check could not run (no network or no `gh` access). "
                "Tell the developer in one line; run the nogamy-core-update skill later.")
    if out.get("update_available"):
        return (f"Nogamy: core {out['latest']} is released; this project has {out['current']}. "
                "Before the task, follow the nogamy-core-update skill from step 3 (offer the update PR). "
                f"Release notes:\n{out.get('notes', '')[:1500]}")
    return f"Nogamy: core is up to date ({out.get('current')}). Say nothing about it unless asked."


def pack_offer(prompt=None):
    """A line for the agent when the project works on a platform whose pack it does not have; else None.
    SessionStart: PROJECT.md `Platform:` or a folder like *.Warehouse. UserPromptSubmit: a platform word.
    At most once a day per project and pack; not for 7 days after the developer said not now."""
    from datetime import date, timedelta
    try:
        from manifest import pack_defs, platform_signal, project_packs, prompt_signal
    except Exception:
        return None
    installed = project_packs(ROOT)
    if installed is None or in_core_repo():  # no Packs line = made before packs: has them all
        return None
    try:
        s = json.loads((tel.HOME / "state.json").read_text(encoding="utf-8"))
    except (OSError, ValueError):
        s = {}
    mine = s.get(str(ROOT).lower(), {})
    today = date.today()
    for name in pack_defs(ROOT) if (ROOT / "nogamy/packs").is_dir() else []:
        if name in installed or mine.get("pack_offered", {}).get(name) == today.isoformat():
            continue
        declined = mine.get("pack_declined", {}).get(name)
        if declined and date.fromisoformat(declined) > today - timedelta(days=7):
            continue
        why = (f"the request mentions '{prompt_signal(prompt, name)}'" if prompt_signal(prompt, name) else None) \
            if prompt is not None else platform_signal(ROOT, name)
        if not why:
            continue
        mine.setdefault("pack_offered", {})[name] = today.isoformat()
        s[str(ROOT).lower()] = mine
        try:
            tel.HOME.mkdir(parents=True, exist_ok=True)
            (tel.HOME / "state.json").write_text(json.dumps(s, indent=2), encoding="utf-8")
        except OSError:
            pass
        tel.emit("pack_offered", None, pack=name, signal="prompt" if prompt is not None else "repo")
        return (f"Nogamy: this project may work on {name} ({why}), but PROJECT.md `Packs:` does not list the "
                f"`{name}` pack. Offer it first, in one line, with the nogamy-add-pack skill. If the developer says "
                f"not now: `python nogamy/ops/core_update.py pack-decline --name {name}`, then go on with the task.")
    return None


def deny(reason):
    decision = {"permissionDecision": "deny", "permissionDecisionReason": reason}
    # Exit 2 blocks in every tool. The JSON is for the tools that read stdout: Copilot (top level and its
    # Claude-compatible hookSpecificOutput), Cursor (permission, agent_message), Gemini CLI (decision, reason).
    print(json.dumps({**decision, "hookSpecificOutput": {"hookEventName": "PreToolUse", **decision},
                      "permission": "deny", "agent_message": reason, "user_message": reason,
                      "decision": "deny", "reason": reason}))
    print(reason, file=sys.stderr)
    return 2


EVENTS = {
    "pretooluse": "PreToolUse", "beforetool": "PreToolUse", "beforeshellexecution": "PreToolUse",
    "beforereadfile": "PreToolUse", "beforemcpexecution": "PreToolUse",
    "sessionstart": "SessionStart",
    "userpromptsubmit": "UserPromptSubmit", "userpromptsubmitted": "UserPromptSubmit",
    "beforesubmitprompt": "UserPromptSubmit", "beforeagent": "UserPromptSubmit",
}
# Other tools' names for the same actions (Gemini CLI; Cursor names: verify against its hook payloads).
TOOL_ALIASES = {
    "write_file": "Write", "replace": "Edit", "edit_file": "Edit", "search_replace": "Edit",
    "run_shell_command": "Bash", "run_terminal_cmd": "Bash", "read_file": "Read",
}


def normalize(d):
    """One shape for every tool: hook_event_name, tool_name, tool_input (in place; returns d)."""
    raw = d.get("hook_event_name") or d.get("hookEventName") or "PreToolUse"
    d["hook_event_name"] = EVENTS.get(str(raw).lower(), raw)
    if str(raw).lower() == "beforeshellexecution" and "command" in d:  # Cursor: the command, no tool name
        d.setdefault("tool_name", "Bash")
        d.setdefault("tool_input", {"command": d["command"]})
    if str(raw).lower() == "beforereadfile" and "file_path" in d:
        d.setdefault("tool_name", "Read")
        d.setdefault("tool_input", {"file_path": d["file_path"]})
    tool = d.get("tool_name") or d.get("toolName")
    if tool in TOOL_ALIASES:
        d["tool_name"] = TOOL_ALIASES[tool]
        d.pop("toolName", None)
        i = enforce_skills.tool_args(d)
        if "absolute_path" in i and "file_path" not in i:  # Gemini read_file
            i["file_path"] = i["absolute_path"]
        d["tool_input"] = i
    return d


def main():
    try:
        d = json.load(sys.stdin)
    except ValueError:
        return 0
    if not isinstance(d, dict):
        return 0
    event = normalize(d)["hook_event_name"]

    if event == "SessionStart":
        tel.emit("session_start", d)
        if daily_check_due():
            # The check itself runs here, so it happens every day; its result becomes the agent's context
            # (SessionStart output → context in Claude Code and Codex). The skill says what to do with it.
            print(daily_check_message())
        offer = pack_offer()
        if offer:
            print(offer)
        return 0
    if event == "UserPromptSubmit":  # stdout becomes context for the agent (Claude Code, Codex)
        offer = pack_offer(d.get("prompt") or d.get("userPrompt") or "")
        if offer:
            print(offer)
        return 0
    if event != "PreToolUse":
        return 0

    m = manifest()
    if m and not in_core_repo():
        hit = core_lock(d, m)
        if hit:
            tel.emit("core_edit_blocked", d, core_path=hit)
            return deny(LOCK_MSG.format(path=hit))

    code, msg, missing = enforce_skills.decide(d)
    if code:
        tel.emit("skill_gate_blocked", d, skill=missing or "base_prompt-section")
        return deny(msg)

    for s in skills_used(d):
        tel.emit("skill_used", d, skill=s, kind="core" if s.startswith("nogamy-") else "project")
    a = agent_used(d)
    if a:
        tel.emit("agent_used", d, agent_name=a, kind="core" if a.startswith("nogamy-") else "project")
    return 0


AGENT_TOOLS = {"agent", "task", "runsubagent", "run_subagent"}


def agent_used(d):
    """The custom agent a tool call starts (Claude Code: Agent/Task + subagent_type; Copilot: runSubagent)."""
    tool = (d.get("tool_name") or d.get("toolName") or "").lower()
    if tool not in AGENT_TOOLS:
        return None
    i = enforce_skills.tool_args(d)
    name = i.get("subagent_type") or i.get("agentName") or i.get("agent_name") or i.get("agent")
    return str(name).split(":")[-1] if name else None


def safe_main():
    """A bug in the hook must not stop the developer's work: report it and let the call go on."""
    try:
        return main()
    except Exception as ex:  # noqa: BLE001
        print(f"Nogamy hook error (the call goes on; please send feedback): {type(ex).__name__}: {ex}",
              file=sys.stderr)
        return 0


if __name__ == "__main__":
    sys.exit(safe_main())
