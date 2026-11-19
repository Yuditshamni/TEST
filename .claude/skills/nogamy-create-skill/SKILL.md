---
name: nogamy-create-skill
description: Add or change a skill in .claude/skills/ so that any AI tool can use it — when a skill is worth writing, core vs project naming, the SKILL.md format, writing rules, a platform reference (references/<platform>.md), registration in PROJECT.md or AGENTS.md, and a dry run. Use when an action was done twice, when a platform needs its own facts, or when asked to create or improve a skill.
---

# Create a skill

## Core skills and project skills

- Core skills are `nogamy-*`. They live in the Nogamy core repo and are **read-only in a project**. A wish to change one → `nogamy-feedback`, never a local edit.
- A project skill is `<project-id>-<what>` (project id from `PROJECT.md` → Identity). Never `nogamy-`, never the name of a core skill.
- Both live in `.claude/skills/` (one home: Claude Code and Copilot load it natively; other tools open it from `AGENTS.md` or `PROJECT.md`). Never copy a skill to `.github/skills/` or `.agents/skills/`.
- In a project: platform facts the project needs are **not** a project skill. They go to `_context/platform.md` §10 → `<skill>`.

## When

- Any action done **twice** becomes a skill.
- A correction the developer had to make twice becomes a line in the matching skill (core skill → `nogamy-feedback`).
- Not a skill: a one-off task, a fact (goes to `_context/`), a decision (goes to `architecture.md`).

## Format (open Agent Skills standard; plain Markdown)

```
.claude/skills/<name>/SKILL.md
---
name: <name>                      lowercase-with-hyphens, same as the folder
description: <what it does + when to use it, with the words a developer would type>
---
# <Title>
## When / Inputs
## Steps
## Rules
## Output
```

- The `description` decides when an agent picks the skill. Put the trigger words in it. At most 1024 characters.
- Up to ~150 lines. Longer → split, or move detail to `references/<topic>.md` in the same folder, pointed to from the skill.
- Extra files (templates, question banks, examples) in the same folder, referenced by relative path.

## Writing rules

- **Tool-neutral.** No instruction that only one AI tool understands. Commands are plain shell, SQL or Python. "Use the tool's plan mode when it has one", never the name of a button.
- **Platform-neutral (core skills).** The skill holds the method. A fact true on one platform only goes to `references/<platform>.md`. A platform skill keeps the `Platform specifics` question table and its standard intro.
- Short lines, one idea each (`nogamy-plan-and-explain`).
- Project facts are linked, not copied: point to `PROJECT.md`, `_context/platform.md`, `_context/architecture.md`, another skill.
- Works at every access level (`AGENTS.md`): say what the AI runs, and what becomes a run sheet when it cannot.
- Examples use invented data. Never sensitive data, never secrets, never a client name in a core skill.
- Say what the agent must **not** do, not only what it does.
- Platform facts are verified in the official docs first (`nogamy-platform-watch`), or tested in DEV and marked so.

## A platform reference (core repo)

A new platform, or more facts for one:
1. `references/<platform>.md` in each platform skill that needs it, answering that skill's `Platform specifics` topics. First line: `# <skill> — <platform>`; second: read when `_context/platform.md` §2 names it.
2. Files only that platform needs (framework objects, tools, MCP config) → a pack: `nogamy/packs/<platform>.txt`, and its detection words in `nogamy/ops/manifest.py` → `SIGNALS`.
3. The watch list of its facts → `nogamy-platform-watch/references/<platform>.md`.
4. A line under "Tech stack" in `AGENTS.md`.

## Register

Same PR:
1. Project skill → a row in `PROJECT.md` → Project skills. Core skill → a row in the skills table of `AGENTS.md`, with its kind.
2. A kind of file that must not be written without it → a rule in `nogamy/hooks/skill-rules.json` (core) or `_context/skill-rules.json` (project; stricter only).
3. If it changes how people work: a line in `HOW-WE-WORK.md` (core) or `_context/working-agreement.md` (project).
4. Core repo: run `python nogamy/ops/validate_core.py`. It fails on a `name` that is not the folder, a long description or skill, a skill missing from `AGENTS.md`, a dangling reference to a `nogamy-` skill that does not exist, or client data.

Worth running in a separate context (a clean-eye review, a lot of output, mechanical work)? Add an agent: `.claude/agents/<name>.md` (core `nogamy-*`, project `<project-id>-*`), registered like a skill.

## Dry run

Give the agent a realistic request without naming the skill. Check that it picks the skill, follows the steps, and stops where it should. Fix the `description` if it was not picked.
Core skill: add a case to `nogamy/evals/cases/` with `must` and `must_not` lines.

A lesson that fits every project, not only this one: `nogamy-feedback`, so it reaches the core.
