# Setup — the Nogamy core repo and its projects

No GitHub App and no client approval: everything a project does with the core runs with the
developer's own GitHub access (`gh auth login`). A Nogamy employee can read the core repo and push
a branch in their project; that is all it needs.

## 1. Once: the core repo (core team, ~15 minutes)

The core repo is `nogamy/core.json` → `core_repo` (today `nogamy-tech/data_eng_template`).

1. Settings → General → **Template repository** ✓.
2. Settings → Secrets and variables → Actions:
   - variable `NOGAMY_IS_CORE_REPO` = `true` (only here; it switches the core-only workflows on and `nogamy-core-guard` off);
   - secret `ANTHROPIC_API_KEY` = for the evals, the curator triage and the fix workflow (without it: evals show as skipped, never as passed);
   - secret `NOGAMY_CLIENT_TERMS` = every client name, GitHub org and system name the core must never contain, comma-separated (the CI blocks any of them).
3. Install the Claude GitHub app on the core repo (github.com/apps/claude), for `nogamy-core-fix`.
4. Branch protection on `main`: PR required; required checks `validate`, `tests`, `live-db` (and `evals` once the key is set).
   Allow the `nogamy-core-release` workflow to push the release commit (or run releases as an admin).
5. Create the branch for usage data: `git switch --orphan usage-data && git commit --allow-empty -m "usage data" && git push origin usage-data`.
6. Labels: `feedback`, `fix-approved`. `core-report` and `control-panel` are created by the curator.
7. Access: every Nogamy developer gets **Write** on the core repo (to open issues with labels and upload usage).
   `main` stays protected, so Write does not let anyone change the core without a PR.
8. Actions → `nogamy-core-release` → Run, version `v0.1.0`. This writes `.core-version` and `nogamy/core-checksums.txt` and creates the release.

## How the core owner steers it

| You want | You do | What happens |
|---|---|---|
| see everything at a glance | open the pinned issue **Nogamy control panel** | rewritten every morning: what needs you, projects behind the latest version, skills used and skipped, files people tried to edit, open feedback |
| a weekly review | the Sunday **Core report** issue | the same, plus an AI triage of the feedback (the 5 most valuable changes) |
| a fix for a feedback issue | label it `fix-approved` | `nogamy-core-fix` opens a PR: the change, an eval case that proves it, validate + tests output. You review and merge |
| a change of your own | a PR to `main` | `validate`, `tests`, `live-db`, `evals` run; merge when green |
| every project to get it | Actions → `nogamy-core-release` | each project gets a core-update PR at its next daily check; its developer merges it |

## 2. A new project (project lead, ~5 minutes)

1. `python tools/new_project.py <owner>/<repo> --clone <folder>` (your own `gh` sign-in, admin on the owner):
   the repo from the template, `main` protected with `nogamy-core-guard` required, cloned.
   A private repo on a free plan cannot be protected: the script says so; record it in `_context/platform.md` §4.
2. Open the folder with an agent and say "set up the project" (`nogamy-project-setup`): it asks about the client,
   platform, environments, Git, promotion and AI access, fills `PROJECT.md` and `_context/`, and offers the
   platform pack. The first core update removes the core-only files; merge that PR.
3. Each developer, once: Python 3.8+ and Git installed; `gh auth login` (with access to the core repo).
   VS Code + Copilot: `chat.useClaudeHooks` is on (the core update writes it to `.vscode/settings.json`).
   Codex: trust the project once (`/hooks`), so `.codex/hooks.json` runs.

### AI tools: where each one gets the rules and the hook

| Tool | Instructions | Skills | Hook (lock + skill gate + usage) | Verified |
|---|---|---|---|---|
| Claude Code | `CLAUDE.md` → `AGENTS.md` | `.claude/skills/` native | `.claude/settings.json` | tests + daily use |
| GitHub Copilot (VS Code) | `.github/copilot-instructions.md` → `AGENTS.md` | `.claude/skills/` native | `.claude/settings.json` via `chat.useClaudeHooks` | event shape tested; Windows shell not yet |
| Codex | `AGENTS.md` | from `AGENTS.md` | `.codex/hooks.json` (after `/hooks` trust) | event shape tested |
| Cursor | `AGENTS.md` | from `AGENTS.md` | `.cursor/hooks.json` | event shape tested from the docs; not run in Cursor yet |
| Gemini CLI | `GEMINI.md` → `AGENTS.md` | from `AGENTS.md` | `.gemini/settings.json` | event shape tested from the docs; not run in Gemini yet |
| A chat in the browser | `python tools/bundle_context.py` → paste | in the bundle | none: the PR check `nogamy-core-guard` is the net | — |

Every config starts `nogamy/hooks/nogamy-hook.sh`, which finds Python 3 and the repo root by itself.
No Python 3 on the machine: tool calls are blocked with what to install, never silently unprotected.
A bug inside the hook never stops the work: the error is shown and `nogamy-core-guard` still checks the PR.

## 3. An existing project (adoption)

On one branch, one PR:
1. Move project facts from `AGENTS.md`, skills and docs into `PROJECT.md` and `_context/`.
2. Rename project-only skills to `<project-id>-<what>` and register them in `PROJECT.md`.
3. Copy the core in: `python <core>/nogamy/ops/core_sync.py --core <core checkout at vX> --project . --version vX --summary sum.md`.
   No `Packs:` line in `PROJECT.md` yet → every pack whose files the project already has is kept and written
   there (a Fabric project keeps `fabric`), so nothing it uses is removed.
4. Keep the project's own workflows (any name not starting with `nogamy-`) and add `nogamy-core-guard` as required.
5. Run `python nogamy/ops/core_guard.py` → `ok`, then the PR.

## 4. A release (core team)

PRs to `main` (validated, evals for changed skills) → Actions → `nogamy-core-release` with the version:
patch = fix, minor = new skill or rule, major = a project must act (say what in the release notes).
Every project sees it at its next daily check. Feedback issues closed since the last release are listed in the notes.

## What runs where

| Piece | Where | Access used |
|---|---|---|
| Lock (hook) | developer machine, every tool call | none |
| Daily core check + update PR | developer machine, session start | developer's `gh` |
| Feedback | developer machine, on request | developer's `gh` (issue in the core repo) |
| Usage upload | developer machine, with the daily check | developer's `gh` (branch `usage-data`) |
| `nogamy-core-guard` | project CI, every PR | default token, project only |
| CI (validate, tests, live-db, evals), release, curator | core repo CI | default token + `ANTHROPIC_API_KEY` |
| Fix PR from feedback (`fix-approved`) | core repo CI | Claude GitHub app + `ANTHROPIC_API_KEY` |
| New project (`tools/new_project.py`) | project lead's machine | the lead's `gh`, admin on the owner |
