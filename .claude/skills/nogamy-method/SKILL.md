---
name: nogamy-method
description: Nogamy's base DWH methodology (standards/base_prompt.md) in short — iron rules, how to label a recommendation, how to behave, the layers, anti-patterns, mines — where each detailed topic lives, and where this project's deviations from the base are recorded. Use before designing anything, and whenever a choice touches the method.
---

# Nogamy method — core

Full source: `standards/base_prompt.md`, never edited in a project. Detailed topics live in the skills (index below). **The project wins only where its deviations table lists it** (below). Need more than this file? Read only the `base_prompt.md` section named in the index (find its heading, read that range), never the whole file.

## Iron rules (base §0; never paraphrase them as optional)

1. Documents first. No infrastructure questions before the documents are collected.
2. STT is a hard prerequisite. No build without an approved STT.
3. One entity at a time, in STT order. A dimension end to end before the next. No fact before its dimensions.
4. Ask about PK / FK / index policy before the first gold table. Once per project.
5. Label every recommendation, in plain words: iron rule / company standard / company recommendation / AI suggestion.
6. Mirror the developer's language. Code and identifiers stay in English.
7. Stay in the current milestone and entity. No drift.
8. Ask before producing large outputs (3+ substantial artifacts).
9. Record decisions at checkpoints (`_context/decisions-log.md`, `nogamy-project-memory`).
10. **Idempotency, no exception path.** A re-run never duplicates and never loses data.

An iron rule is overridden only when the developer asks explicitly; say it is a deviation, wait for confirmation, log it. The AI never invokes an exception by itself.

## How to behave (base §2, §11)

- Not sure which label? Pick the weaker one. Never over-claim "company standard".
- When in doubt, ask. Never assume. One question at a time, with options (`_context/working-agreement.md`; the base allows 2–3, Nogamy is stricter).
- A conflict with an iron rule or a company standard is said out loud, never followed silently.
- Lead: say what comes next.
- Plans and explanations: `nogamy-plan-and-explain`.

## Layers

| Base | Role |
|---|---|
| PRE_BRONZE | landing for a source that needs a merge by key, or re-delivers keys (`nogamy-bronze-load`) |
| BRONZE | the source as is + ETL columns. No business logic |
| SILVER | all business logic, in views, as few as stay readable; every load goes view(s) → silver staging → gold (`nogamy-db-objects`) |
| GOLD | star model, the persistent truth (`nogamy-db-objects`, `nogamy-build-table`) |
| SERVE | optional: views on gold only, no tables and no load (`SERVE.V_<TABLE>`); by default the BI model reads gold |
| MNG | config, watermark, migration log |

**Own lane, no needless dependency.** Each dimension and fact loads only through its own layers: its bronze tables → its silver view(s) → its silver staging → its gold table. It never reads another entity's silver view, silver staging or gold table, unless that is truly needed. A needed dependency stays, and is written down: what it reads and why (`nogamy-db-objects`).

**Simplest that stays readable.** Every extra object is one more thing the next developer has to open. As few views as stay readable; a watermark only where bronze accumulates; one shape for every load.

## Where each topic lives

| Topic | Base § | Skill |
|---|---|---|
| all names and prefixes | §0.2.1, pipeline methodology §1 | `nogamy-naming` |
| documents, STT checklist, build order | §5.1 | `nogamy-specs` |
| config, load patterns, ETL columns, watermark, PRE_BRONZE | §3a | `nogamy-bronze-load` |
| silver views, `-99`, `KEY_<ENTITY>`, load procedure, SCD, PK / FK, style | §4, §4.9–4.12, §8 | `nogamy-db-objects` |
| build one entity end to end | §4 | `nogamy-build-table` |
| quality framework, end-to-end QA, testing rules | §4a, §6b, §9 | `nogamy-qa-checks` |
| pipelines, master pattern, run order, gates | pipeline methodology | `nogamy-build-pipeline` |
| self code review | §6a | `nogamy-review` |

## Deviations: where this project differs from the base (project wins)

This skill is core and read-only in a project. The project's deviations live in the project:
- the table: `_context/architecture.md` → section `Deviations from the base` (add the section the first time);
- a rule that binds every agent: also a line in `PROJECT.md` → Project rules.

Read that table before a design choice. A choice it does not list → the base applies.
Filled at setup (`nogamy-project-setup`) and whenever a deviation is decided. A row needs a reason and who decided. `to confirm` = also a row in `_context/open-questions.md`. Logged in the decisions log (`nogamy-project-memory`).

Format of the table:

| Base method | Here | Why | Decided by | Status |
|---|---|---|---|---|

Deviations that projects often take, to consider at setup (not decided until written in the project's table):
- spec as Markdown per target table in `stt/`, the workbook exported for sign-off (Nogamy default);
- `_context/architecture.md` (current truth) + a decisions log (history), instead of one decisions file;
- one file per object + a numbered migration per change, instead of one unified script per entity (Nogamy default);
- no SERVE views: the BI model reads gold;
- fewer silver views than the five-view chain: one by default, split where a real subquery or a second job appears;
- one load shape (view(s) → silver staging → gold); the gold step by table: full reload for dimensions and small tables, match by key + watermark for delta;
- a config table per source system only where many tables share a pattern; a direct pipeline otherwise;
- PRE_BRONZE only for sources that re-deliver keys;
- `MERGE` (update only on business change) instead of delete + insert by logical key;
- a `QA` schema for the data-quality framework, instead of its tables in `MNG`;
- a project prefix on object names when several projects share one database, or none when they do not.

## Anti-patterns: only with an explicit, logged approval (base §0.2.2)

Extra bronze helper tables · indexes beyond the agreed policy · partition columns · `IS_DELETED` columns · extra ETL columns, `ROW_NUMBER` / `BATCH_ID` / `RUN_ID` / `SOURCE_SYSTEM` columns · logging tables · master or cleanup procedures · surrogate-key generators · multi-source `UNION`. Name it, label it as AI suggestion, ask.

## Mines: raise as questions, never assume

`FACT_KEY` collisions · late-arriving data · schema drift · time zones · `NULL` vs `''` vs `'N/A'` · hard-coded filters · STT ≠ code · missing `IS_LAST` filter · CTE pyramid in silver · hidden dependency on another entity's layers · fact before its dimensions · missing watermark update · quality checks passing while the data is wrong (a person still looks at 100 rows of every new table).

On Microsoft Fabric (`_context/platform.md` §2): `references/fabric.md`.
