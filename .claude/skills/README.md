# .claude/skills/ — the one home of the skills

Claude Code and GitHub Copilot load these natively; Codex and any other tool open them from the table in `AGENTS.md`.

- `nogamy-*` = core: read-only in a project (a change → `nogamy-feedback`). Platform facts: `references/<platform>.md` inside a skill.
- `<project-id>-*` = this project's own skills, registered in `PROJECT.md` (`nogamy-create-skill`).
- Never copy a skill to `.github/skills/` or `.agents/skills/`: Copilot would list it twice.
