"""Checks the core before a merge or a release (core repo only). Standard library only.

    python nogamy/ops/validate_core.py            exit 1 on any error

1. The manifest loads and every entry matches at least one file.
2. Every nogamy-* skill: frontmatter name = folder, a description (<= 1024 chars), <= 150 lines, a row in AGENTS.md,
   and every file in its references/ named in SKILL.md.
3. No dangling skill reference (`nogamy-x` named in a core file but no such skill).
5. No client data in core files: pii_gate patterns, and the words in env NOGAMY_CLIENT_TERMS
   (comma list, a secret of the core repo: every client name, org, system the core must never contain).
6. Every .py compiles.
7. Packs (nogamy/packs/*.txt): every entry and seed matches a file, no path in two packs, no seed is core,
   and the pack paths that core-manifest.txt also lists are said once (in the pack).
8. Every hook config (Claude Code, Codex, Cursor, Gemini CLI) starts nogamy/hooks/nogamy-hook.sh on its
   tool-call, session-start and prompt events.
"""
import json
import os
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(Path(__file__).resolve().parent))
from manifest import Manifest, pack_defs  # noqa: E402
import pii_gate  # noqa: E402

MAX_SKILL_LINES = 150
MAX_DESCRIPTION = 1024  # Agent Skills limit
TEXT = {".md", ".py", ".yml", ".yaml", ".json", ".sql", ".txt", ".toml", ".ps1", ".sh"}
GATE_SKIP = {"nogamy/ops/pii_gate.py", "nogamy/core-checksums.txt", "nogamy/ops/validate_core.py", "nogamy/evals/cases/feedback-scrub.json"}  # invented PII on purpose; release hashes
KNOWN_NON_SKILLS = {"nogamy-core", "nogamy-core-update", "nogamy-core-guard", "nogamy-feedback-relay",
                    "nogamy-core-release", "nogamy-core-curator", "nogamy-core-evals", "nogamy-core-ci",
                    "nogamy-feedback-sent", "nogamy-feedback-blocked", "nogamy-core-bot", "nogamy-org",
                    "nogamy-core-src", "nogamy-hook", "nogamy-telemetry", "nogamy-core-fix", "nogamy-test"}


def main():
    errors, warnings = [], []
    m = Manifest.load(ROOT, installed="all")
    files = m.core_files(ROOT)
    every = [f.relative_to(ROOT).as_posix() for f in ROOT.rglob("*")
             if f.is_file() and not {".git", "__pycache__"} & set(f.relative_to(ROOT).parts)]
    packs = pack_defs(ROOT)
    stored = {name: m.stored_files(ROOT, name) for name in packs}
    for name, r in packs.items():
        for e in r.include:
            if not any(Manifest._match(e, f) or f == e.rstrip("/") for f in stored[name]):
                errors.append(f"pack {name}: entry matches no file in nogamy/packs/{name}/: {e}")
        for e in r.seeds:
            if not m.source(ROOT, e).is_file():
                errors.append(f"pack {name}: seed is not a file in nogamy/packs/{name}/: {e}")
            elif m.base.matches(e):
                errors.append(f"pack {name}: seed {e} is also in core-manifest.txt (a seed is never core)")
        for f in stored[name]:
            if not (r.matches(f) or f in r.seeds):
                errors.append(f"pack {name}: nogamy/packs/{name}/{f} is stored but not listed in {name}.txt")
    for f in every:  # the template root holds no platform files: a pack file lives only in nogamy/packs/<name>/
        owner = next((n for n, r in packs.items() if r.matches(f) or f in r.seeds), None)
        if owner and not f.startswith("nogamy/packs/"):
            errors.append(f"{f}: a `{owner}` pack file at the template root; keep it only in nogamy/packs/{owner}/{f}")
    for f in sorted({f for fs in stored.values() for f in fs}):
        owners = [n for n, r in packs.items() if r.matches(f)]
        if len(owners) > 1:
            errors.append(f"{f}: in two packs ({', '.join(owners)})")

    for e in m.include:
        if not any(Manifest._match(e, f) or f == e.rstrip("/") for f in files):
            warnings.append(f"manifest entry matches no file: {e}")

    agents = (ROOT / "AGENTS.md").read_text(encoding="utf-8")
    skills = sorted(p.name for p in (ROOT / ".claude/skills").iterdir() if p.is_dir() and p.name.startswith("nogamy-"))
    for s in skills:
        f = ROOT / ".claude/skills" / s / "SKILL.md"
        if not f.exists():
            errors.append(f"{s}: no SKILL.md")
            continue
        head = f.read_text(encoding="utf-8").split("---")
        fm = head[1] if len(head) > 2 else ""
        name = re.search(r"^name:\s*(\S+)", fm, re.M)
        if not name or name.group(1) != s:
            errors.append(f"{s}: frontmatter name must be '{s}'")
        if not re.search(r"^description:\s*\S", fm, re.M):
            errors.append(f"{s}: no description")
        lines = len(f.read_text(encoding="utf-8").splitlines())
        if lines > MAX_SKILL_LINES:
            errors.append(f"{s}: {lines} lines, max {MAX_SKILL_LINES} (nogamy-create-skill); move detail to references/")
        desc = re.search(r"^description:\s*(.+)$", fm, re.M)
        if desc and len(desc.group(1)) > MAX_DESCRIPTION:
            errors.append(f"{s}: description is {len(desc.group(1))} characters, max {MAX_DESCRIPTION}")
        if f"`{s}`" not in agents:
            errors.append(f"{s}: no row in the AGENTS.md skills table")
        # A platform reference nobody is told about is never read: every references/<platform>.md is named in SKILL.md
        text = f.read_text(encoding="utf-8")
        for ref in sorted((f.parent / "references").glob("*.md")) if (f.parent / "references").is_dir() else []:
            if f"`{ref.name}`" not in text and f"references/{ref.name}" not in text:
                errors.append(f"{s}: references/{ref.name} is not named in SKILL.md (add it to the `shipped:` list)")

    # Agents: .claude/agents/nogamy-*.md, Claude format (Copilot in VS Code reads the same file)
    agent_dir = ROOT / ".claude/agents"
    core_agents = sorted(p.stem for p in agent_dir.glob("nogamy-*.md")) if agent_dir.is_dir() else []
    for s in core_agents:
        parts = (agent_dir / f"{s}.md").read_text(encoding="utf-8").split("---")
        fm = parts[1] if len(parts) > 2 else ""
        name = re.search(r"^name:\s*(\S+)", fm, re.M)
        if not name or name.group(1) != s:
            errors.append(f"agent {s}: frontmatter name must be '{s}'")
        if not re.search(r"^description:\s*\S", fm, re.M):
            errors.append(f"agent {s}: no description")
    section = agents.split("## Agents", 1)[1].split("\n## ", 1)[0] if "## Agents" in agents else ""
    rows = set(re.findall(r"^\|\s*`(nogamy-[a-z0-9-]+)`", section, re.M))
    for s in sorted(set(core_agents) - rows):
        errors.append(f"agent {s}: no row in the AGENTS.md Agents table")
    for s in sorted(rows - set(core_agents)):
        errors.append(f"AGENTS.md Agents table: `{s}` has no file .claude/agents/{s}.md")
    if (ROOT / ".github/agents").exists():
        errors.append(".github/agents/ exists: agents have one home, .claude/agents/ (Copilot would list them twice)")
    named = set(skills) | set(core_agents)

    for f in files:
        p = m.source(ROOT, f)
        if p.suffix.lower() not in TEXT:
            continue
        text = p.read_text(encoding="utf-8", errors="ignore")
        for ref in set(re.findall(r"`(nogamy-[a-z0-9-]+)`", text)) if f not in GATE_SKIP else ():
            if ref not in named and ref not in KNOWN_NON_SKILLS:
                errors.append(f"{f}: names `{ref}` but there is no such skill or agent")
        if f not in GATE_SKIP:
            for r in pii_gate.check(text, _client_terms()):
                code_noise = p.suffix in (".py", ".yml", ".yaml") and r.startswith(("connection string", "private key"))
                if not r.startswith("link outside") and not code_noise:
                    errors.append(f"{f}: {r}")
        if p.suffix == ".py":
            try:
                compile(p.read_bytes(), str(p), "exec")  # in memory: no .pyc written, same on every OS
            except (SyntaxError, ValueError) as ex:
                errors.append(f"{f}: does not compile: {str(ex).strip()[:120]}")


    # One hook, wired for each tool: every config starts the same launcher on its own names for the same events.
    hook_cfgs = (
        (".claude/settings.json", ("PreToolUse", "SessionStart", "UserPromptSubmit")),
        (".codex/hooks.json", ("PreToolUse", "SessionStart", "UserPromptSubmit")),
        (".cursor/hooks.json", ("preToolUse", "beforeShellExecution", "beforeReadFile", "sessionStart",
                                "beforeSubmitPrompt")),
        (".gemini/settings.json", ("BeforeTool", "SessionStart", "BeforeAgent")),
    )
    for cfg, events in hook_cfgs:
        try:
            hooks = json.loads((ROOT / cfg).read_text(encoding="utf-8"))["hooks"]
        except (OSError, ValueError, KeyError):
            errors.append(f"{cfg}: missing or not valid JSON")
            continue
        for ev in events:
            cmds = [h.get("command", "") for g in hooks.get(ev, []) for h in (g.get("hooks") or [g])]
            if not any("nogamy/hooks/nogamy-hook.sh" in c for c in cmds):
                errors.append(f"{cfg}: {ev} does not run nogamy/hooks/nogamy-hook.sh")
    for dup in (".github/skills", ".agents/skills"):
        if (ROOT / dup).exists():
            errors.append(f"{dup}/ exists: skills have one home, .claude/skills/ (Copilot would list them twice)")

    for w in warnings:
        print(f"warning: {w}")
    for e in errors:
        print(f"error: {e}")
    in_packs = sum(1 for f in files if m.pack_of(f))
    print(f"{len(files)} core files ({in_packs} in packs: {', '.join(packs) or 'none'}), {len(skills)} core skills, {len(core_agents)} core agents, {len(errors)} errors, {len(warnings)} warnings")
    return 1 if errors else 0


def _client_terms():
    return [t.strip() for t in os.environ.get("NOGAMY_CLIENT_TERMS", "").split(",") if len(t.strip()) >= 3]


if __name__ == "__main__":
    sys.exit(main())
