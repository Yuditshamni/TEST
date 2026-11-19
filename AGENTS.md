# AGENTS.md — Nogamy data project

The single source of instructions for every AI tool here, coding agents and chat tools alike.
Tool files (`CLAUDE.md`, `GEMINI.md`, `.github/copilot-instructions.md`) only point here and override nothing.
One hook guards every tool the same way (`nogamy/hooks/`).

This file is **core**: the same in every project and platform. Project facts: `PROJECT.md` and `_context/`.

> **Not set up?** If `_context/platform.md` says `status: not set up`, run `nogamy-project-setup` before anything else.

## Read in this order

1. This file.
2. `PROJECT.md`: client, project id, platform and packs, environments, people, project skills, agent tools, project rules.
3. `_context/platform.md`: stack, Git, promotion, change model, AI access level, data sensitivity, platform notes per skill.
4. `_context/architecture.md` (current truth) and `_context/open-questions.md` (never assume on an open item).
5. `_context/working-agreement.md`.
6. The skill for the task and the `README.md` of the folder you touch.
7. `standards/base_prompt.md` only when `nogamy-method` is not enough: find the section heading, read that range. Never the whole file.

## Daily, first session of the day

1. `nogamy-core-update`: the session-start hook checks for a newer core; offer the update PR.
2. `nogamy-platform-watch`: if `last_checked` in `_context/platform-facts.md` is not today, re-check the facts that can expire.

## Core and project

- **Core files are read-only in a project** (list: `nogamy/core-manifest.txt`; includes every `nogamy-*` skill, agent and workflow, `standards/`, `tools/`, `nogamy/`, folder READMEs and templates, an added pack's files). Never edit one, not even a typo. The hook blocks it; `nogamy-core-guard` fails the PR.
- **Core change wanted → `nogamy-feedback`**: drafted without client data, shown, sent as an issue after approval. The fix returns in a core update.
- **Core updates**: daily check → PR → a person merges (`nogamy-core-update`). Version: `.core-version`.
- **Platform references**: every skill is generic; what is true on one platform only is in the skill's `references/<platform>.md`, read when `_context/platform.md` §2 names it. Project additions: §10.
- **Platform packs** (`nogamy/packs/`, listed in `PROJECT.md` → `Packs:`): files only one platform needs. A new project has none; missing one → `nogamy-add-pack`. An added pack is core.
- **Project additions**: facts → `PROJECT.md`, `_context/`. Skills → `.claude/skills/<project-id>-<what>/`, agents → `.claude/agents/<project-id>-<what>.md`, both registered in `PROJECT.md`. Workflows → any name not starting with `nogamy-`.
- **A project rule may be stricter than the core, never looser.** On conflict the core wins and the conflict becomes feedback.
- **Usage is measured**: skill or agent used, when, project, what a hook blocked. Never prompts, contents or data (`nogamy/docs/telemetry.md`; `PROJECT.md` → `Telemetry:`).

## Hard rules

- **Setup first.** No design or code before `_context/platform.md` is filled.
- **Architecture decisions belong to the architect** (`PROJECT.md` → People and roles). Task needs an open one → stop, name it and its owner.
- **Skill before file.** Before writing or changing a file, open the skill for its kind (`nogamy/hooks/skill-rules.json`).
- **Plan first, always.** Every change starts with a plan the developer approves (`nogamy-plan-and-explain`).
- **Explain in very short, very simple lines**, one idea each, each clear on its own. After the plan, at most one light multiple-choice question.
- **AI proposes, a human approves**, through the review path in `_context/platform.md` §4 (branch → PR by default). Nothing directly on the main branch.
- **AI works only in DEV, at its access level.** Never TEST or PROD. The AI never promotes.
- **AI never** deletes data or objects, never changes permissions.
- **AI never sees sensitive rows**: structure, counts, sums, test or masked data only (§8). No real people or customers in prompts, files or examples. Exception: the project's own people in `_context/people-and-access.md` (name, role, e-mail; never a phone).
- **Nothing about a client leaves the project**: feedback, usage and anything sent to Nogamy carry no personal or client data, no client name beyond the project id.
- **No secrets** in the repo, the chat or a file. Identity config lives in `_private/` (Git-ignored).
- **Documents are Markdown only.** One exception: `docs/`, for final, signed or approved documents (`docs/README.md`). Received material → `.md` before it enters `_private/raw/`. Code and platform item files are fine.
- **Where the AI puts a document:** final and signed or approved → `docs/`. Anything else → `_private/docs/`. What a person put in `docs/` stays there.
- **`docs/` is read only when asked.** It is an archive for maintaining the project, never a source of truth. The truth is the Markdown in `_context/`, `sources/`, `stt/`, `qa/`.
- **Not final → temporary**: a session temp table or the `TRY_` marker, never on the main branch (`nogamy-db-objects`).
- **Same names in every environment.** No `dev`/`test`/`prod` in any name, no environment in code. Reference `schema.object`. Per-environment values: §5.
- **Idempotent, no exception.** A re-run never duplicates and never loses data.
- **Verify first.** Any platform fact (feature, limit, syntax, API) is checked in official docs, not memory (`nogamy-platform-watch`).
- **Proof, not claims.** "Done" comes with what ran and what came out. Not run → say so, with the reason.
- **Three failed attempts at the same thing → stop**, report what was tried and what you suspect.
- **"Update" = edit the existing file**, never a parallel one. One fact, one place.
- **One file, one owner.** Another role's file: PR, not a direct edit.

## What the AI can run here

Level: `_context/platform.md` §7. Until set: L0.

| Level | The AI can | A person does |
|---|---|---|
| **L0** files only | read and write repo files | runs everything, pastes back counts and errors |
| **L1** SQL read | + query structure, counts, sums in DEV | runs every change |
| **L2** SQL write | + run migrations, procedures, checks in DEV | runs ETL jobs and pipelines |
| **L3** full loop | + publish and run ETL items in DEV, commit, drift check | reviews, pushes, merges |

- What the AI cannot run, it hands over as a **run sheet**: exact commands in order, expected result of each; the person pastes results back (`nogamy-dev-workflow`).
- At L3 the agent runs the whole DEV loop after plan approval, handing no step over unless asked.
- Checks are the same at every level; only who presses Run changes. Never say something ran before a person confirms it.

## Skills (`.claude/skills/`)

Claude Code and Copilot load them natively; any other tool opens `.claude/skills/<name>/SKILL.md` from this table. Never copy a skill to `.github/skills/` or `.agents/skills/` (Copilot lists it twice).
**M** = method, same on any stack. **P** = platform: generic frame + `references/<platform>.md` + `_context/platform.md` §10.

| Skill | Kind | Use for |
|---|---|---|
| `nogamy-project-setup` | M | new project: platform, Git, promotion, AI access; fills `PROJECT.md`, `_context/` |
| `nogamy-plan-and-explain` | M | every task: plan first, short self-contained lines |
| `nogamy-project-memory` | M | reading and updating `PROJECT.md`, `_context/`; after a meeting |
| `nogamy-method` | M | base method: iron rules, labels, layers, anti-patterns, deviations |
| `nogamy-naming` | M | every name: schemas, objects, columns, jobs, files, branches |
| `nogamy-specs` | M | `sources/`, `stt/`, export for client sign-off |
| `nogamy-explore-data` | M | profile a table without reading sensitive values |
| `nogamy-legacy-migration` | M | legacy BI / ETL → sources, joins, rules, measures, STT drafts |
| `nogamy-build-table` | M | a dimension or fact from an approved STT |
| `nogamy-qa-checks` | M | per-table checks, end-to-end QA, golden questions |
| `nogamy-reconcile-numbers` | M | new DWH vs legacy vs source, before numbers leave the team |
| `nogamy-review` | M | checklist on every change before a person reviews |
| `nogamy-troubleshoot` | M | failed run, error, wrong numbers, refused deployment |
| `nogamy-client-readout` | M | read a deliverable as the client before sending |
| `nogamy-create-skill` | M | add or change a project skill (never a core one) |
| `nogamy-platform-watch` | M | platform facts, checked daily against official docs |
| `nogamy-feedback` | M | "feedback: …" — a core gap or bug, sent without client data |
| `nogamy-core-update` | M | daily: newer core? open the "core update" PR |
| `nogamy-add-pack` | M | the project's platform pack is missing from `Packs:` |
| `nogamy-dev-workflow` | P | any task end to end: plan → build → run (or run sheet) → self-check → commit → drift → hand over |
| `nogamy-git-workflow` | P | branches, commits, PR, who pushes, what never enters Git |
| `nogamy-deploy` | P | promotion between environments; deployment note, test document |
| `nogamy-write-sql` | P | queries in the project's SQL dialect |
| `nogamy-db-objects` | P | one file per object, migrations, load procedure, try-outs |
| `nogamy-bronze-load` | P | load pattern per source table, config, ETL columns, watermark |
| `nogamy-build-pipeline` | P | ETL / orchestration items: naming, order, gates, no hard-coded environment |
| `nogamy-semantic-model` | P | BI model: descriptions, synonyms, measures, RLS, AI-ready |

## Agents (`.claude/agents/`)

Fresh context, limited tools, none edits files. Claude Code and Copilot in VS Code load them natively; any other tool runs `.claude/agents/<name>.md` as a separate fresh pass, not reusing its own reasoning.
Allowed commands come from `PROJECT.md` → Agent tools; a missing command → the agent stops and says so. Never copy an agent to `.github/agents/`.

| Agent | Use for | Can |
|---|---|---|
| `nogamy-code-reviewer` | every PR, before a person: where the change breaks | read; commands marked `Writes: no` |
| `nogamy-data-qa` | after a DEV run, before a PR or numbers leave the team | read; `read-only query` only |
| `nogamy-source-profiler` | a new source system or table; one per source, in parallel | read; `source read-only query` only |
| `nogamy-client-reviewer` | anything that goes to the client | read |

## Chat tools (no repo access)

Run `python tools/bundle_context.py` and paste the bundle: this file, `PROJECT.md`, `_context/` and the skills named (`tools/README.md`).

## Repo map

Owner in brackets; another owner's file → PR. **[core]** = read-only here. Folder details: each `README.md`.

- `AGENTS.md`, tool files, `.claude/skills/nogamy-*`, `.claude/agents/nogamy-*`, `.github/workflows/nogamy-*`, hook config, `nogamy/`, `standards/`, `tools/` [core; `tools/project/` is the project's]
- `PROJECT.md` [project lead] · `_context/` [shared, per file]
- `sources/` [systems analyst] · `stt/` one spec per target table [analyst + data engineer]
- `db/` one file per object · `etl/` · `scripts/` numbered migrations, seed, grants [data engineer]
- `bi/` models and reports as text [BI developer] · `ui/` report specs, mockups [BI developer + analyst]
- `qa/` `data/` checks, `deploy/` test documents, `golden/` questions [shared]
- `docs/` final, signed or approved documents (Office and PDF allowed); read only when asked [project lead]
- `_private/` local only, Git-ignored: received material, outputs for people, notes
- A platform whose Git integration fixes the layout (Fabric: `fabric/data/`, `fabric/bi/`) uses it instead of `db/` `etl/` `bi/` (skill reference; `_context/platform.md` §4).

Received → `_private/raw/`. For the AI → `_context/`, `sources/`, `stt/`. For people → `_private/docs/`. Signed or approved, final → `docs/`.

## Language and writing

- Structure in English: files, headings, columns, keys, objects, code comments. Business values in the client's language (Hebrew by default): descriptions, synonyms, rules, golden questions. Never both in one identifier.
- One fact, one place. Tables and lists over prose. Explicit, never "as usual".
- Commits small: `<scope>: <what> — <why>`. Names: `nogamy-naming`.

## Tech stack

Any; the project's is in `PROJECT.md` → `Platform:` and `_context/platform.md` §2.
Core references today: `fabric` (Warehouse + T-SQL · Data Factory · Power BI), `sqlserver` (SQL Server, Azure SQL), `adf`, `airflow`. Other platforms work from the generic skills and §10 until a reference is added (`nogamy-feedback`).
