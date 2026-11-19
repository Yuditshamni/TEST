# Nogamy data project starter (Nogamy core)

The skeleton every new Nogamy data project starts from ("Use this template"): one repo where the systems analyst, the data engineer, the BI developer and an AI tool work on the same text.

It does not depend on an AI tool, a database, an ETL tool or a BI tool. Platforms Nogamy already worked on (Microsoft Fabric) come with ready knowledge and tools. The project decides those in its first hour (`nogamy-project-setup` skill), and the answers are written into the repo.

- **Starting a project?** [`START-HERE.md`](START-HERE.md) (Hebrew).
- **Joining a project?** [`HOW-WE-WORK.md`](HOW-WE-WORK.md).
- **An AI tool?** [`AGENTS.md`](AGENTS.md).

## Structure

```
AGENTS.md            instructions for every AI tool (single source)
START-HERE.md        how to open a new project from this starter
HOW-WE-WORK.md       the working guide for people
PROJECT.md           the project's facts: client, project id, platform and packs, environments, people
.claude/skills/      how each kind of task is done — one home, every AI tool reads it (nogamy-* = core)
.claude/agents/      helpers with a fresh context: code reviewer, data QA, source profiler, client reviewer
nogamy/              the core machinery: manifest, platform packs, the one hook, updates, feedback, evals
standards/           Nogamy's method (read-only in a project)
_context/            project memory: platform, architecture, open questions, glossary, rules
sources/             what exists in the source systems
stt/                 what we build: one spec per target table
db/                  database objects, one file per object
etl/                 ingestion and orchestration items, as text
bi/                  semantic models and reports, as text
scripts/             migrations (every database change), seed, grants
ui/                  report specs and mockups
qa/                  data checks, test documents per deploy, golden questions
tools/               small scripts the team and the AI run
_private/            local only, never committed
```

Every folder has a `README.md` saying what belongs in it.

## The ideas inside

| Idea | Where |
|---|---|
| One instruction file for every AI tool | `AGENTS.md` |
| The project's memory is files, not chat history | `_context/`, skill `nogamy-project-memory` |
| A setup interview before any code: platform, Git, promotion, AI access | skill `nogamy-project-setup` → `_context/platform.md` |
| The analyst writes specs as text; code, checks and the BI model are derived from them | `sources/`, `stt/`, skill `nogamy-specs` |
| Open questions have an owner and never hide inside a spec | `_context/open-questions.md` |
| Plan before change; explanations in short self-contained lines | skill `nogamy-plan-and-explain` |
| The loop works at any access level: what the AI cannot run becomes a run sheet for a person | `AGENTS.md`, skill `nogamy-dev-workflow` |
| Every database change = the object file + a numbered, re-runnable migration | `db/`, `scripts/` |
| Every deploy has a test document with expected results, filled per environment | `qa/deploy/`, skill `nogamy-deploy` |
| Try-outs are temporary or marked `TRY_`, and never reach the main branch | skill `nogamy-db-objects` |
| The AI never sees sensitive rows, never touches TEST or PROD, never promotes | `AGENTS.md` |
| Platform facts are verified in the official docs, and re-checked | skill `nogamy-platform-watch` |

| Generic skills; platform knowledge in `references/<platform>.md` (Fabric today); files for one platform as a pack | `.claude/skills/`, `nogamy/packs/`, skill `nogamy-add-pack` |
| Core files are read-only in a project; projects get core updates as a daily PR | `nogamy/core-manifest.txt`, skill `nogamy-core-update` |
| What a project learns comes back to the core, cleaned of client data | skill `nogamy-feedback`, `nogamy/docs/how-it-works.md` |

## Changing the core

This repo is the Nogamy core. It is changed here, never inside a project (there the hook blocks it).
A project sends what it learned with `nogamy-feedback`; the core team changes the core by PR, CI runs `nogamy/ops/validate_core.py` and the evals, and a release reaches every project as a core update PR.
How it works: `nogamy/docs/how-it-works.md`. First-time setup of the core repo: `nogamy/docs/setup.md`.
