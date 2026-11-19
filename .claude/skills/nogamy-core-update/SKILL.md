---
name: nogamy-core-update
description: Once a day, check whether a newer Nogamy core is released and, if the developer agrees, open the "core update vX.Y.Z" PR with their own GitHub access. Use at the first session of the day (the session-start hook reminds you), or when the developer says "core update", "עדכון ליבה", "is there a new core", "update the skills".
---

# Daily core update

The core (skills, AGENTS.md, standards, tools, framework) comes from the Nogamy core repo.
A project never edits it; it takes new versions through this skill, as a PR the developer merges.

## When

- First session of the day in this repo (the session-start hook says so), before the task.
- The developer asks for it.
- Skip it when the developer is in the middle of urgent work and says so; it asks again tomorrow.

## Steps

1. `python nogamy/ops/core_update.py check` — once a day; `--force` only if the developer asks.
   It also uploads the day's usage events (metadata only).
2. `checked_today` or `update_available: false` → one line ("core is up to date, vX") and go on with the task.
3. Update available → tell the developer in at most 5 short lines:
   current → latest, what changed (from `notes`), whether it says **framework** or **breaking** (major version).
   Ask: "Open the core update PR now?" (options: yes / not today).
4. Yes → `python nogamy/ops/core_update.py apply --version <latest>`.
   - Uncommitted changes → it stops. Ask the developer to commit or stash; never stash for them.
   - It creates `nogamy/core-update-<v>`, applies the core, pushes, opens the PR, and returns to the original branch.
   Give the PR link. Say: "Review and merge it yourself". If the PR body warns about framework objects,
   say a migration is needed before TEST (`nogamy-deploy`).
5. Not today → `python nogamy/ops/core_update.py decline --version <latest>`. One line. Go on with the task.

## Rules

- Never merge the PR, never push to `main`, never edit core files by hand to "help" the update.
- Never resolve a conflict inside a core file by keeping the project's version: core files are the core's.
  A conflict in a project file (e.g. `PROJECT.md`) → stop and show it to the developer.
- `gh` not logged in or no access to the core repo → say so in one line (`gh auth login`, access via the
  core team) and go on with the task. Do not retry.
- No core repo configured (`nogamy/core.json` has a placeholder) → skip silently.
