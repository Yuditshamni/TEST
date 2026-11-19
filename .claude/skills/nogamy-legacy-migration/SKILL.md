---
name: nogamy-legacy-migration
description: Turn the system being replaced (a BI tool's load scripts and expressions, an older DWH's procedures, report definitions, Excel logic) into project files — source tables used, joins, business rules, measures, STT drafts. Use when starting a new domain of a migration, or when someone asks "how does the old system calculate X".
---

# From the legacy system to the DWH

The old system is the best documentation of the business rules, and the number users will compare us to.

The system being replaced: `PROJECT.md` → Identity → `Replaces`. Its own file layout and expression language: `references/<tool>.md` in this folder (shipped: `qlik.md`).

## Inputs (read-only, `_private/raw/reference/`)

Whatever the legacy system can export, converted to Markdown (`nogamy-project-memory`):

| Kind | Holds |
|---|---|
| load or ETL scripts | sources, joins, transformations, filters |
| data model export | tables, keys, relationships |
| metadata of reports and apps | dimensions, measures, expressions, sheets |
| shared logic (common dimensions, include files) | logic every app reuses |
| procedures and views of an older database | the same, as SQL |
| the client's own maps and documents | their view of the model |

List the inputs that exist in `sources/README.md` or the domain's notes, so the next person knows what was read.

## Steps, one app or subject area at a time

1. **Sources**: every source table the script reads → a file in `sources/<system>/` if missing (`nogamy-specs`), with `used_by_legacy: <app>`.
2. **Joins**: every join key → `sources/<system>/relationships.md`, with the script line as evidence.
3. **Rules**: every filter, mapping or condition (`IF`, `CASE`, a lookup) that carries business meaning → `_context/business-rules.md` (`BR-NNN`, status `draft`, source: `<app>, <script section>`).
4. **Measures**: every expression → `_context/legacy-measures.md` (app, sheet, name, expression as is). `meaning_he` and `in_use` stay for the analyst. Do not translate to the BI language here: `nogamy-semantic-model` drafts the measures from this file.
5. **STT drafts**: the target tables the app implies → `stt/<domain>/<table>.md`, status `draft`, with a "from legacy" note per column.
6. **Golden questions**: the numbers users look at every day → `qa/golden/<domain>.md`, status `draft`.
7. List what is unclear → `_context/open-questions.md`, owner: the analyst or the client contact (`PROJECT.md` → People and roles).

## Rules

- Copy logic, do not improve it silently. A legacy behaviour that looks wrong → an open question, not a fix.
- Quote the script line (file + section) for every rule and join.
- Never copy data values from legacy files into examples.
- Finish one app before the next. Which one first is the project lead's choice.
- Dead logic counts: a measure nobody uses is marked `in_use: no` by the analyst, and is not migrated.
- Show the list of what was found before writing the files (`nogamy-plan-and-explain`).
- No legacy system in the project → `_context/legacy-measures.md` says "none", and `nogamy-reconcile-numbers` compares with the source only.
