@AGENTS.md

Claude Code notes (core file; everything else is in `AGENTS.md` above):
- Skills are in `.claude/skills/` and agents in `.claude/agents/`; both load natively. Still open the skill the task needs before writing (`AGENTS.md` → Skill before file).
- One hook for every tool: `nogamy/hooks/nogamy_hook.py`, wired in `.claude/settings.json`. It blocks edits to core files, enforces skill-before-file (`nogamy/hooks/skill-rules.json`), blocks reading `standards/base_prompt.md` whole, runs the daily core check at session start, offers a missing platform pack, and records usage (`nogamy/docs/telemetry.md`).
- Your own settings and permissions: `.claude/settings.local.json` (not in Git). `.claude/settings.json` is core.
