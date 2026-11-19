"""PreToolUse hook (Claude Code and GitHub Copilot): skill before file, base_prompt by section only.

Exit 2 blocks the tool call; the stderr text goes back to the agent.
Rules: AGENTS.md (hard rules "Skill before file" and reading order step 7).
The rules are data: nogamy/hooks/skill-rules.json (core), and _context/skill-rules.json (project,
optional, same shape, checked first; it can only add rules). A path matches from the repo root.
The command uses a path relative to the repo root: Copilot does not set CLAUDE_PROJECT_DIR.
"""
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def load_rules():
    """[(path prefix, ending or None, skill)] — project rules first, then core; first match wins."""
    rules = []
    for f in (ROOT / "_context" / "skill-rules.json", ROOT / "nogamy" / "hooks" / "skill-rules.json"):
        try:
            data = json.loads(f.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            continue
        rules += [(r["path"], r.get("ext"), r["skill"]) for r in data.get("rules", []) if "path" in r and "skill" in r]
    return rules


def rel(path):
    p = norm(path)
    root = norm(str(ROOT)).rstrip("/") + "/"
    if p.lower().startswith(root.lower()):
        p = p[len(root):]
    while p.startswith("./"):
        p = p[2:]
    return p

READ_TOOLS = {"Read", "view"}
WRITE_TOOLS = {"Write", "Edit", "MultiEdit", "create", "edit"}

# Copilot loads a skill with its `skill` tool; the tool result reads: Skill "<name>" loaded successfully
COPILOT_SKILL_LOADED = re.compile(r'Skill "([\w-]+)" loaded successfully')


def norm(p):
    return (p or "").replace("\\", "/")


def tool_args(d):
    i = d.get("tool_input") or d.get("toolArgs") or {}
    if isinstance(i, str):
        try:
            i = json.loads(i)
        except ValueError:
            i = {}
    return i if isinstance(i, dict) else {}


def skills_opened(transcript_path):
    """Skill names this session opened; None when there is no transcript to check."""
    if not transcript_path:
        return None
    try:
        lines = open(transcript_path, encoding="utf-8").readlines()
    except OSError:
        return None
    opened = set()
    for line in lines:
        opened.update(COPILOT_SKILL_LOADED.findall(line.replace('\\"', '"')))
        try:
            d = json.loads(line)
        except ValueError:
            continue
        if not isinstance(d, dict) or d.get("type") != "assistant":
            continue
        for c in (d.get("message") or {}).get("content") or []:
            if not isinstance(c, dict) or c.get("type") != "tool_use":
                continue
            i = c.get("input") or {}
            if c.get("name") == "Skill" and i.get("skill"):  # Claude Code loaded the skill natively
                opened.add(str(i["skill"]).split(":")[-1])
                continue
            text = norm(i.get("file_path") or i.get("command") or "")
            if "/skills/" in text and "SKILL.md" in text:
                for part in text.split("/skills/")[1:]:
                    opened.add(part.split("/")[0])
    return opened


def decide(d):
    """(exit code, message, missing skill or None) for one hook event. Called by nogamy_hook.py."""
    tool = d.get("tool_name") or d.get("toolName")
    i = tool_args(d)
    path = norm(i.get("file_path") or i.get("path") or i.get("filePath"))

    if tool in READ_TOOLS and path.endswith("standards/base_prompt.md") and not (i.get("limit") or i.get("view_range")):
        return 2, ("base_prompt.md is never read whole (AGENTS.md). Grep the section heading, "
                   "then read it with a line range."), None

    if tool in WRITE_TOOLS:
        r = rel(path)
        for prefix, ext, skill in load_rules():
            if r.startswith(prefix) and (ext is None or r.endswith(ext)):
                opened = skills_opened(d.get("transcript_path") or d.get("transcriptPath"))
                if opened is not None and skill not in opened:
                    return 2, (f"Skill before file (AGENTS.md): read .claude/skills/{skill}/SKILL.md "
                               f"before writing {path.split('/')[-1]}."), skill
                break
    return 0, "", None


def main():
    code, msg, _ = decide(json.load(sys.stdin))
    if msg:
        print(msg, file=sys.stderr)
    return code


if __name__ == "__main__":
    sys.exit(main())