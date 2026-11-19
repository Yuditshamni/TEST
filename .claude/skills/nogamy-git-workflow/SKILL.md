---
name: nogamy-git-workflow
description: How work moves through Git in this project — topic branches, small commits, what a PR must contain, who commits and who pushes, what never enters Git, core files that are read-only, and how definitions get between the platform and the repo when the platform does not sync with Git by itself. Use when starting a task, committing, preparing a PR, or when asked how code gets into the repo.
---

# Git workflow

The facts (provider, address, approvers, sync) are in `_context/platform.md` §4 and `PROJECT.md` → DevOps. This skill is how we use them.

## The repo is the source

- What is in Git is the truth. DEV is a place where the truth is tried.
- An object that exists only in DEV, or only in someone's tool, does not exist for the project.
- The platform syncs with Git by itself, and it is usable here → use it, and say in "Platform specifics" which direction is allowed (tool → Git, Git → tool).
- It does not, or it is blocked → the repo is written first, DEV is filled from it, and the two are compared before every PR (`nogamy-dev-workflow` step 5). How a definition travels in each direction is in "Platform specifics".

## Core files and project files

- **Core files are read-only in a project**: `AGENTS.md`, `nogamy-*` skills and agents, `standards/`, `tools/`, `nogamy/`, and the files of an installed pack (list: `nogamy/core-manifest.txt`). A write to one is blocked, and the `nogamy-core-guard` check fails a PR in which a core file differs from the release.
- A wish to change a core file → `nogamy-feedback`. Never a local edit, never a commit that "fixes" it.
- New core versions arrive only as a `core update vX.Y.Z` PR from `nogamy-core-update`. **A person reviews and merges it**; the AI never merges it and never resolves a conflict inside a core file.
- Project facts live in `PROJECT.md` and `_context/`. Project skills are `.claude/skills/<project-id>-<what>/`, registered in `PROJECT.md` → Project skills; never `nogamy-`.

## Branches

- One topic, one branch: `feature/<what>`, `stt/<what>`, `context/<topic>` (`nogamy-naming`). `nogamy/core-update-<v>` belongs to `nogamy-core-update`.
- Never work on the main branch. On it by mistake → create the branch before the first change.
- Short-lived: a branch that lives for weeks collides with the migration numbers of others (`scripts/README.md`).

## Commits

- Small and focused: `<scope>: <what> — <why>`. The message says why.
- Only the files of this task. Never "add all".
- A decision and its record travel together: the change to `architecture.md` and the line in the decisions log are one commit (`nogamy-project-memory`).
- **The AI commits only when the developer asks.** It never commits secrets, Office files, or anything under `_private/`.

## Push and PR

- **The AI never pushes and never merges**, unless `_context/platform.md` §4 says otherwise and the developer asks in that session. (`nogamy-core-update` and `nogamy-add-pack` push their own PR branch with the developer's access; a person still merges.)
- Before the PR, the AI runs `nogamy-review` on the branch (agent `nogamy-code-reviewer`) and fixes what is critical.
- The PR description holds:

```
What and why: <2–3 lines>
Files: <by kind: specs / db objects / migrations / ETL items / checks>
Checks: <per-table checks, both runs, who ran them>
Test document: qa/deploy/<branch topic>.md (DEV column filled)
Deployment note: <see `nogamy-deploy`>
DEV cleanup before merge: <try-out objects dropped by hand, or "none">
Not run / known issues: <or "none">
```

- A person approves. The author of a change does not approve their own PR where the repo's rules allow a second person.
- Automatic checks (CI, `nogamy-core-guard`) that fail are fixed, not bypassed.

## What never enters Git

| Never | Where it goes |
|---|---|
| passwords, keys, tokens, connection strings with credentials | the platform's secret store / the OS credential store |
| rows of people or customers, also inside examples and test files | nowhere; use invented data |
| Office files, PDF, archives, exports for people | `_private/docs/`; only a final, signed or approved document → `docs/` (`docs/README.md`) |
| material as received | `_private/raw/` |
| internal notes, people commentary, commercial terms | `_private/` |
| try-out objects (`TRY_`) | a branch only, never the main branch |

A secret was committed by mistake → stop, tell the developer. Removing the file is not enough: the secret is rotated.

Nothing about the client leaves the project: not in feedback, not in telemetry, not in a core file.

## No Git yet

The client has not given a repo: `git init` locally and work the same way, with a person responsible for the backup of the folder. The first push happens when the repo exists; nothing in the method waits for it.

## Platform specifics

> Skills are core and read-only in a project. Platform facts come from, in order:
> 1. `references/<platform>.md` in this folder, for each platform named in `_context/platform.md` §2 (shipped: `sqlserver.md`, `adf.md`, `airflow.md`).
> 2. `_context/platform.md` §10 → `nogamy-git-workflow`: what this project adds or overrides.
> 3. Neither exists → the table below is the question list: fill the answers in `_context/platform.md` §10 at setup (`nogamy-project-setup`), verified in the official docs (`nogamy-platform-watch`).

| Topic | This project |
|---|---|
| Provider, repo, main branch | ? |
| How the repo is reached (VPN, account) | ? |
| Who approves a PR; required checks (incl. `nogamy-core-guard`) | ? |
| Who merges core-update PRs (`PROJECT.md` → People and roles) | ? |
| May the AI push or open a PR? | no (default) |
| Platform ↔ Git sync: exists? used? which direction? | ? |
| Tool → file: how a definition is exported | ? |
| File → tool: how a definition is published | ? |
| Text formats in the repo (database, ETL, BI) | ? |
| Not in Git, and where it is recorded | ? |
