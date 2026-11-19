# PROJECT.md — <project name>

The facts of this project. Owned by the project; the core never overwrites this file.
Core files (`AGENTS.md`, `nogamy-*` skills, `standards/`) never name a client. They point here.
Read it right after `AGENTS.md`. Filled by `nogamy-project-setup`; the technical profile is `_context/platform.md`.

## Identity

- Client: <client name>
- Project id: <short-kebab-id>   (label on feedback issues and usage events; same in every tool)
- Never in feedback: <client words that must never leave the project: org name, Git org, system and product names>
- Telemetry: on   (on / anonymous / off — `nogamy/docs/telemetry.md`)
- Platform: <e.g. Fabric / SQL Server / Snowflake / Databricks / PostgreSQL / BigQuery>   (the hook offers the matching pack, if one exists)
- Packs: none   (core parts per platform: `nogamy-add-pack`; a PR may add a pack, never remove one)
- Scope: <first subject area, e.g. HR>
- Replaces: <legacy system, if any>
- Reports: <BI tool>

## Environments

Names only, no secrets. What each holds and who may change it: `_context/platform.md` §3.

- DEV: <workspace / database / server>      the only environment the AI works in
- TEST: <name>                               people only
- PROD: <name>                               people only
- BI: <names, if separate>                   people only
- AI identity (DEV only): <service principal / user name, or "none: the AI works at L0">

## Sources

| Source system | Folder under `sources/` | Load method | Notes |
|---|---|---|---|
| <system> | `<folder>` | <full / delta / merge> | |

## People and roles

- Architect (owns architecture decisions): <name>
- Data engineer(s): <names>
- BI developer(s): <names>
- Systems analyst: <name>
- Approves core updates (`nogamy-core-update` PRs): <name>
- People and access detail: `_context/people-and-access.md`

## Documents

- Architecture and working procedures: `_private/docs/<file>` (local, ignored)

## DevOps (project-owned)

- PR checks: <workflow file, e.g. `.github/workflows/pr-validations.yml`>
- Promotion: <workflow files or manual steps — `_context/platform.md` §5>
- Branch protection on `main`: required checks must include `nogamy-core-guard`.

## Project skills

Skills written for this project only: `.claude/skills/<project-id>-<what>/` (never `nogamy-`), made with `nogamy-create-skill`.

| Skill | Use for |
|---|---|

## Agent tools

The commands the agents (`AGENTS.md` → Agents) may run in this project, for its platform.
A command missing here → the agent stops and says so. `Writes: no` = safe for read-only agents.

| Tool | Command | Writes |
|---|---|---|
| diff | `git diff main...HEAD` | no |
| offline checks | <command> | no |
| drift check (repo vs DEV) | <command, or "none"> | no |
| read-only query | <command, or "none"> | no |
| source read-only query | <command, or "none"> | no |

## Project agents

Agents written for this project only: `.claude/agents/<project-id>-<what>.md` (never `nogamy-`).

| Agent | Use for |
|---|---|

## Project rules

Additions to `AGENTS.md`. A project rule may be stricter than the core, never looser.
To change a core rule: `nogamy-feedback`, not a local override.

-

### Naming

The project's and the client's naming choices (`nogamy-naming`: source column **P** / **C**). Only what differs from the core defaults.

| Item | Rule | Source (P / C) | Status |
|---|---|---|---|
| Project prefix | <none / `<PREFIX>_`> | P | |
