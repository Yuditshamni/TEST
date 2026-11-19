---
name: nogamy-project-setup
description: First task in a new project started from the Nogamy core template — collect the documents, then ask about the project, the platform (database, ETL, BI), the environments, Git, how a change is promoted between environments (manual, platform tool, CI/CD), what the AI can run, and data sensitivity; fill PROJECT.md and _context/, add the platform pack if one exists, and record the platform notes per skill. Use when the status in _context/platform.md is "not set up", when asked to set up, kick off or onboard a project, or when the platform, the Git flow or the promotion path changes.
---

# Project setup

Nothing is designed or built before this skill has run. Its product is not code: it is a repo that knows where it lives.
Core files (`AGENTS.md`, `nogamy-*` skills, `standards/`, `tools/`, `nogamy/`) are not edited here: they are the same in every project. Setup writes only project files.

## When

- `_context/platform.md` has `status: not set up`.
- Later, in part: a new environment, a new Git or promotion path, a new AI tool, a change of access level, a new platform. Then only the matching block of questions runs.

## Steps

### 1. Documents first (iron rule)

Ask what already exists, before any question: proposal or statement of work, architecture documents, the client's standards (naming, security, Git, deployment), lists of sources, meeting summaries, anything about the system being replaced.

- Each one is converted to Markdown into `_private/raw/` (`nogamy-project-memory`).
- Read them. Every answer found in a document is written down with its source, and **not asked again**.

### 2. The interview

Question bank: `questions.md` in this folder, blocks A to H.

- **One question at a time**, with 2–4 options where a choice exists. Use the tool's choice buttons when it has them.
- Order: A → H. Git (D) and promotion (E) are never skipped: they decide how every later task ends.
- Skip a question a document already answered; show the answer in one line and move on.
- **"I don't know" is a valid answer.** It becomes a row in `_context/open-questions.md` with an owner (a role or a person) and what it blocks. Never guess, never pick a default silently.
- An answer that is an architecture decision (layers, storage, transformation tool) belongs to the architect. If the person answering is not the architect: record it as open, owner = architect.
- After each block: write the answers to their file (`PROJECT.md` or `_context/platform.md`, per `questions.md`), show the block as written, continue.

### 3. The platform (after block B)

1. Write `PROJECT.md` → `Platform:`.
2. **Pack.** If `nogamy/packs/<platform>.txt` exists (today: `fabric`) → `nogamy-add-pack`. It opens its own PR; setup goes on meanwhile.
3. **Core reference.** For each platform skill (kind **P** in `AGENTS.md`), check whether `references/<platform>.md` exists in its folder. Write the answer in `_context/platform.md` §2 and §9.
4. Neither exists → the project works from the generic skills. Say so in one line. A platform Nogamy will meet again → suggest `nogamy-feedback` ("add a core reference for <platform>").

### 4. Prove the access

Whatever access level was declared (block G), prove it before relying on it:

| Level | Proof |
|---|---|
| L0 | hand the person one harmless query (list the schemas); they paste the result |
| L1 | run that query yourself in DEV |
| L2 | create and drop one temp table in DEV |
| L3 | run one existing, harmless ETL item in DEV and read its status |

Write the command and its result in `_context/platform.md` §7, and the commands the agents may run in `PROJECT.md` → Agent tools.
It did not work → the level is the last one that did, and the gap is an open question with the exact error.

### 5. Fill the repo

| File | What is written |
|---|---|
| `PROJECT.md` | Identity (client, project id, never-in-feedback words, telemetry, platform, scope, replaces, reports), Environments (names only), Sources, People and roles, DevOps, Agent tools |
| `_context/platform.md` | every section; `status: set up <date>`; remaining `?` only where an open question exists |
| `README.md` | title and first paragraph for this project |
| `_context/architecture.md` | only what was decided, by the architect; deviations from the base method in its own section |
| `_context/open-questions.md` | every unanswered question: owner, what it blocks |
| `_context/working-agreement.md` | the project lead's preferences, where they differ from the defaults |
| `_context/platform-facts.md` | `last_checked`, and the first verified facts (`nogamy-platform-watch`; the watch list in `references/<platform>.md` of that skill, if there is one) |
| `_context/people-and-access.md` | the people (name, organization, role, e-mail; never a phone), access, who approves what |
| `_context/decisions-log.md` | a first entry: the setup decisions, dated |
| `_private/` | folders from `_private/README.md` |
| folders not used in this project (`bi/`, `ui/`, or `db/` `etl/` when the platform's layout replaces them) | a line in `_context/architecture.md` → "Not used", with the reason (folder READMEs are core). Never delete a folder |

`AGENTS.md` is not edited: it is core. The project's own lines go to `PROJECT.md`.

### 6. The platform notes per skill

For each platform skill, in this order: `nogamy-git-workflow`, `nogamy-deploy`, `nogamy-dev-workflow`, `nogamy-write-sql`, `nogamy-db-objects`, `nogamy-bronze-load`, `nogamy-build-pipeline`, `nogamy-semantic-model`:

1. Read its `Platform specifics` question table, and its `references/<platform>.md` if there is one.
2. Propose, for `_context/platform.md` §10 → `<skill>`, only what this project adds or overrides, from the answers and the official docs (`nogamy-platform-watch`: verified, never from memory).
3. The developer approves each one. Update §9 (`core reference`, `§10`, both, or `not used`).

A question still open stays `?` in §10, and its open question says so. Do not fill §10 with guesses. Never copy the core reference into §10: §10 holds differences only.

### 7. Hand over

```
## Setup — <project>
Decided: <one line per block>
Platform: <name> · pack: <added (PR link) / none exists> · core reference: <skills with references/<platform>.md / none>
Open: <n> questions — the ones that block work, with owners
Access proved: L<n> — <command> → <result>
Platform notes: <skills with §10 entries / all from the core reference / still generic>
First steps: analyst → <e.g. sources/<system>> · data engineer → <e.g. migration 0001, first bronze table> · BI → <…>
```

Commit (when asked): `context: project setup`.

## Rules

- No secrets are asked for, and none are written. Server names and accounts yes; passwords, keys and tokens never.
- Names of people: roles and names in `PROJECT.md` → People and roles; e-mail and access in `_context/people-and-access.md`. Phone numbers are never written.
- Do not start designing during setup. An idea that comes up → one line in `open-questions.md`.
- The interview can stop and resume: `PROJECT.md` and `platform.md` show what is filled. On resume, read them and continue from the first `?`.
- A chat tool without file access (L0, no repo): the answers are written as the full text of `PROJECT.md` and `platform.md`, for the person to save.
- A setup step that seems to need a core change (a rule, a template, a skill) → `nogamy-feedback`, never a local edit.
