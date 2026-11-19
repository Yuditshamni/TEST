---
name: nogamy-db-objects
description: How to write database objects in the repo — one file per table, view, procedure or function, a numbered migration for every change, temp tables or TRY_ for anything not final, silver views (as few as stay readable), own lane, the -99 row, and the load procedure chosen by load type (full reload, delta, SCD2). Use whenever writing or changing a .sql file under db/.
---

# Database objects

Names: `nogamy-naming`. Dialect: `nogamy-write-sql`. Method source: `standards/base_prompt.md` §4, §4.10–4.12.

Detail files (open only when the task needs them):
- `references/load-procedure-templates.md`: the frame of a full-reload and a delta procedure.
- `references/try-outs-and-dev-cleanup.md`: the `TRY_` lifecycle, cleaning DEV before a PR.
- `references/<platform>.md`: folders, limits and the procedure frame of the platform in `_context/platform.md` §2 (shipped: `fabric.md`, `fabric-load-procedure-templates.md`, `sqlserver.md`, `sqlserver-load-procedure-templates.md`).

## Where

```
db/<SCHEMA>/<Tables|Views|Procedures|Functions>/<OBJECT>.sql
```

(A platform reference may set another root and folder names. The rules stay.)

- One object = one file = one `CREATE`: how the object looks now. To change an object, edit its file.
- **Every change also gets a numbered migration** in `scripts/migrations/` (create, alter, add column, drop, data move). Migrations are what reach every environment (`scripts/README.md`).
- Grants → `scripts/grants/`. Config rows → `scripts/seed/`.
- Renaming: new object file, old file deleted; one migration creates the new, moves the data, drops the old.

## Anything not final: a temp table, or `TRY_`

A permanent object nobody can tell apart from a real one is a trap: it gets deployed, or it gets depended on, and the repo-vs-DEV check cannot tell it from drift.

| What | How | Example |
|---|---|---|
| real object of the approved plan (default) | its final name | `GOLD.SALES_DIM_CUSTOMER` |
| try-out inside one session (an intermediate step, a comparison, a debug copy) | a session temp table | `#CUSTOMER_CHANGES` |
| try-out that must outlive the session (a demo, a load run by pipelines, a comparison over days) | `TRY_` before the full object name, on every object of the try-out | `GOLD.TRY_SALES_DIM_CUSTOMER` |

- **Which one is the developer's choice.** The AI asks before building whenever the work is called a test, a demo or a try-out, or the plan does not say: "final names or `TRY_`?". No answer → do not build.
- Never a permanent `TEST_` / `TMP_` / `DEV_` name: `TRY_` is the one marker, so one search finds every try-out.
- **`TRY_` never reaches the main branch.** The AI never deletes: leftovers are reported, the developer drops them (`references/try-outs-and-dev-cleanup.md`).

## Before the first gold table (iron rule)

Ask the PK / FK / index policy once for the project: none (base default) / PK on the logical key (not enforced where the platform cannot) / per table. Write the answer in `_context/architecture.md`. Where the platform does not enforce a constraint, uniqueness is proven by checks (`nogamy-qa-checks`).

## Simplest that stays readable, uniform where it counts

Every extra object is one more thing the next developer has to open to understand a load.

- **Flexible, by readability:** the number of silver views; a watermark only where bronze accumulates.
- **Uniform, always:** every entity loads view(s) → silver staging → gold, in one procedure; every gold table has the same ETL columns (`IS_LAST_UPDATE_IND`, `ETL_INSERT_DATE`, `ETL_UPDATE_DATE`). Same shape for a full reload and a delta. One way to read every load.

## Silver: views

**As many views as readability needs, no more.**

- Start with **one** view: `SILVER.V_<PROJECT>_<TABLE>`. A simple entity (one source, no keys to look up) stays one view.
- Split into a new view when keeping one would need: a real subquery or a CTE pyramid; two unrelated jobs in one `SELECT` (key lookups, then heavy business rules); the same intermediate result twice.
- Each view does one readable job and can be queried alone. Business logic lives in views, never inside the procedure.
- Typical: a dimension from one source → 1 view; a fact with several lookups → 2–3. The plan says how many and why.
- Always, in one view or many: read bronze with `IS_LAST_INSERT_TO_BRONZE_IND = 1` (also correct for a full bronze, where every row is `1`).

When split, the steps take these names (skip a step that would do nothing):

| View | Does |
|---|---|
| `_STEP1_SOURCE` | source columns; the bronze filter; carries `LOAD_TO_BRONZE_TS` (delta only) |
| `_STEP2_KEYS` | business keys, `FACT_KEY`, `KEY_<ENTITY>` lookups |
| `_STEP3_NA` | unmatched keys → `-99` |
| `_STEP4_ETL` | transformations from the STT |
| `_FINAL_STEP` | final column list, exactly as the gold table |

## Own lane: what an entity may read

| An entity's silver views read | Allowed? |
|---|---|
| its own bronze tables, its own earlier silver views | yes, always |
| a dimension's gold table, from a fact's `_STEP2_KEYS`, to resolve `KEY_<ENTITY>` and `-99` | yes: the standard needed dependency |
| another entity's silver view or silver staging | no. Silver staging is that load's temporary copy, not a source |
| another gold table for any other reason | only when truly needed. Say why in the plan, wait for approval |

A dependency that stays is documented in the header comment of the view that reads it (`-- Depends on: GOLD.SALES_DIM_CUSTOMER (KEY_CUSTOMER lookup, -99 mapping)`), and in the run order (`nogamy-build-pipeline`).

**Development map.** `db/DEV_MAP.md` is generated by `python tools/dev_map.py`, never edited by hand. Any change to a file under `db/` → run it and commit the map in the same commit. An unexpected dotted arrow = a dependency nobody planned: fix it, or document it (Own lane).

## Dimension: the `-99` row

One row with key `-99` (`'-99'` for text keys), name "unknown" in the client's language. Facts map unmatched keys to `-99`, never NULL.

- Full reload: the view returns it (`UNION ALL`). Nothing in the procedure.
- Delta load: the procedure inserts it if missing.

## Load procedure: one per entity, always the same two steps

1. **Silver staging**: empty `SILVER.SILVER_<PROJECT>_<TABLE>`, insert from the last view. Freezes this load once; everything after reads the staging table, not the view.
2. **Gold**: write gold from staging, by the pattern of the table:

| Gold load | When | Step 2 | Watermark | `IS_LAST_UPDATE_IND` |
|---|---|---|---|---|
| **Full reload** | dimensions and small tables; the view returns the whole table | empty gold + insert from staging | no | always `1` |
| **Delta, match by key** (base default) | bronze accumulates; only new or changed rows reach silver | mark gold `IS_LAST_UPDATE_IND = 0`, delete gold rows whose key is in staging, insert staging | yes | `0` previous, `1` this load |
| **Delta, merge** | the same, updating only on a business change | merge from staging | yes | `1` |
| **SCD2** | history per version | close the old version (`VALID_TO`, `IS_CURRENT_FLAG`) + insert | yes | `1` |

- The pattern per table comes from the STT. Not stated → ask, do not default.
- Always: one transaction; on error roll back and raise; the row counts of staging and gold returned as a result; idempotent (twice = same result).
- The procedure moves data. It holds no business logic.
- Silver staging columns: the gold columns without `ETL_UPDATE_DATE`; plus `LOAD_TO_BRONZE_TS` when there is a watermark.
- The watermark moves inside the transaction, only on success (`nogamy-bronze-load`).
- An empty bronze would empty gold: the bronze gate (`Empty_Table`) runs before, so the procedure never sees an empty source.
- Writing the procedure → copy the frame from `references/load-procedure-templates.md` (or the platform's version of it).

## Style (company standard)

SQL keywords UPPERCASE · explicit joins · a header comment on every procedure and view (what it loads, the pattern, why this many views) · divider `--------------------------------------------------------` · no commented-out code · long column lists one per line.

## Before you finish

- [ ] one file per object, `CREATE` only, right folder; names per `nogamy-naming`
- [ ] a numbered migration for the change, applied in DEV; object file and migration agree
- [ ] view(s) → silver staging → gold in every procedure; no extra view or watermark; the plan says why
- [ ] no permanent work tables; work done in temp tables
- [ ] `-99` row and mapping; `KEY_<ENTITY>`, `FACT_KEY` in facts
- [ ] the load run twice → same result
- [ ] delta loads: watermark updated inside the transaction, only on success
- [ ] `db/DEV_MAP.md` regenerated

## Platform specifics

Skills are core and read-only in a project. Platform facts come from, in order:
1. `references/<platform>.md` in this folder, for each platform named in `_context/platform.md` §2 (shipped: `fabric.md`, `sqlserver.md`).
2. `_context/platform.md` §10 → `nogamy-db-objects`: what this project adds or overrides.
3. Neither exists → the table below is the question list: fill the answers in `_context/platform.md` §10 at setup (`nogamy-project-setup`), verified in the official docs (`nogamy-platform-watch`).

| Topic | This project |
|---|---|
| Folder root and folder names for object files | ? |
| Types to use for text, numbers, dates, flags | ? |
| Constraints and indexes: what exists, what is enforced | ? |
| What `ALTER TABLE` can and cannot do; what needs a new table + copy | ? |
| Transactions, error handling, `MERGE`: syntax and limits | ? |
| Temp table syntax and scope | ? |
| Does a truncate roll back inside a transaction? | ? |
| Backup of one table before a risky change (clone, copy, snapshot) | ? |
| How migrations are applied to DEV | default: `python tools/run_migrations.py --profile <dev> [--as-agent]` (sqlserver, fabric, snowflake, postgres, databricks); L0 or another platform: `--run-sheet`; or the project's own tool: ? |
| A different transformation tool (not SQL procedures): how this contract maps to it | ? |
| Known traps | ? |
