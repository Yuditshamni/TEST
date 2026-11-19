---
name: nogamy-bronze-load
description: Design and build the bronze layer — load pattern per source system and table, config-driven ingestion where a source warrants it, ETL columns, merge load with soft deletes and its mass-delete guard, the bronze→gold watermark for delta loads, and the quality gate after every bronze load. Use when adding a source or a source table, choosing a key, or changing how one loads.
---

# Bronze

Source: `standards/base_prompt.md` §3a (company standard unless marked). Names: `nogamy-naming`.

Detail files (open only when the task needs them):
- `references/merge-load.md`: the full merge rules, the mass-delete guard, a new merge table. Open before building or changing a merge load.
- `references/oracle-source.md`: an Oracle source (types, casts, ETL columns in the source query).
- `references/<platform>.md`: how the platform lands and merges (shipped: `fabric.md`, `fabric-merge-load.md`, `fabric-oracle-gateway.md`, `adf.md`, `airflow.md`).

## Before the first source

The framework objects (config table, watermark table, the quality framework) must be on the main branch, not only in DEV. Before relying on them, check they have files and migrations there.

## Principles

- Bronze = the source as is + ETL columns. History accumulates. No business logic.
- The load pattern is decided **per source system**, then per table where the source differs. It is written in `sources/<system>/README.md` and in each table's file. A source with retroactive changes or deletes → `FULL_MERGE`, not `DELTA`. An inconsistent source → raise it.
- **Idempotent:** a re-run of the same window never duplicates (iron rule).
- **A failed load never empties bronze.** Land the extract in a staging table (`PRE_BRONZE`) first; touch bronze only when the extract arrived whole.
- Types come from the source's catalog, never from a column's name.

## Load patterns

| Pattern | Staging holds | Bronze after the load | Source deletes | Use when |
|---|---|---|---|---|
| `FULL` | — | truncated and reloaded | gone with the truncate | a table with no key yet; small reference tables |
| `FULL_MERGE` | the whole source table | merged by key: insert new, update changed, leave unchanged untouched | soft delete (`DELETED_DATE`) | a table with a key and no trustworthy change column |
| `DELTA` | one window, by the change column | merged by key | not detected by a window | a large table with a change column that moves on **every** change |
| `Delta_Month` / `Daily_Insert` / `Date_Range` | one period | that period replaced | within the period | event data that arrives by date or month |

- A key is needed for every merge. Choosing it: `nogamy-explore-data` (unique on the data), then the business confirms.
- `DELTA` only after proof: a full copy compared by key with what the delta produced. A gap → back to `FULL_MERGE`.
- Deletes in a `DELTA` table need their own design (a periodic full compare, or a signal from the source): an open question until designed.

## Config table: per source system, not for everything

The base recommends one config table for every bronze source. It is decided **per source system**, by what it buys:

| Use a config table + a master item that loops over it | Use a direct item per source |
|---|---|
| many tables, same connection, same pattern | a source with its own logic: an API with tokens and paging, files, one-off tables |
| a new table should be one config row, not a new item | fewer than a handful of tables |

- The cost of config: what runs is hidden in a table row, and debugging goes through one more layer. The cost without: one item per table.
- The choice and its reason go in `sources/<system>/README.md`. Not decided → ask, do not default.
- Where config is used (`MNG.MNG_BRONZE_CONFIGURATION`, one row per source table, base column names in UPPERCASE): items read the rows with `IS_ACTIVE = 1`; nothing source-specific is typed into an item.

| Column | Meaning |
|---|---|
| `SOURCE_SYSTEM`, `SOURCE_GROUP`, `SOURCE_NAME` | where it comes from |
| `SOURCE_QUERY` | project addition: the query sent to the source, where the tool needs one |
| `EXTRACT_MODE` | the load pattern |
| `TARGET_TABLE_NAME`, `TARGET_TABLE_KEYS` | the bronze table and its logical key |
| `LAST_FROM_DELTA`, `LAST_TO_DELTA` | the extraction window |
| `LAST_BUSINESS_SUCCESSFUL_LOAD_DATETIME`, `LAST_INSERT_TO_BRONZE_DATETIME` | run bookkeeping |
| `IS_ACTIVE` | `1` / `0`. A row is disabled, never deleted |
| `IS_MASS_DELETE_APPROVED` | `1` releases the mass-delete guard for one run; a successful run resets it |

- On success: advance the window. On failure or a failed gate: **do not** advance; the next run retries the same window.
- Window: from = last `to` minus a safety overlap; to = when the load **started** (UTC), never when it ended. A row changed during the load must fall in the next window.
- A one-off re-load of other dates: a special-dates row overrides the window for one run (`IS_DONE = 0` → use it, then set `1`; rows kept for audit).

## ETL columns (the contract between bronze and silver)

| Column | Purpose |
|---|---|
| `LOAD_TO_BRONZE_TS` | when the row landed or last changed; passed through every silver view |
| `IS_LAST_INSERT_TO_BRONZE_IND` | `1` = not yet confirmed into gold. Silver always reads bronze with `= 1`, also for `FULL` loads |
| `ETL_INSERT_DATE` / `ETL_UPDATE_DATE` | row bookkeeping |
| `DELETED_DATE` | project addition: NULL unless the row left the source (merge loads). Not on `PRE_BRONZE` tables or `FULL` tables |

The first four columns are on every bronze table.

## Merge load (`FULL_MERGE`, `DELTA`)

Bronze keeps a row untouched unless a column changed, so gold receives only changes, and a failed extract does not empty bronze. Full rules: `references/merge-load.md`.

1. Extract lands in `PRE_BRONZE.PRE_<bronze table>` (truncated first).
2. Gate on staging: `Duplicates` on the key (the merge needs one row per key).
3. One merge procedure per source system (`BRONZE.SP_LOAD_BRONZE_<SYSTEM>`): guard (`FULL_MERGE` only), flag what gold confirmed, merge.

- Compare keys and columns NULL-safely: with a plain `=`, a NULL in a key inserts a new row on every run.
- Never delete rows in the merge, and never treat "missing from the extract" as deleted when the extract is a window.
- **Mass-delete guard (before any write):** staging empty while bronze has active rows → stop, no approval releases this. Missing keys above a threshold (a count **and** a share of the active rows) → stop, unless `IS_MASS_DELETE_APPROVED = 1`. Stop = the step fails, bronze is unchanged, the window does not advance.

## Watermark: delta loads only (company standard)

Needed only when bronze **accumulates** and gold loads a **delta**. A full bronze feeding a full-reload gold table needs no watermark and no seed row (`nogamy-db-objects`).

`MNG.MNG_BRONZE_GOLD_DELTA`: one row per bronze → gold pair (`BRONZE_TABLE_NAME`, `GOLD_TABLE_NAME`, `MAX_CONFIRMED_BRONZE_TS`, `ETL_UPDATE_DATE`).

- The gold load sets `MAX_CONFIRMED_BRONZE_TS` to the newest `LOAD_TO_BRONZE_TS` it loaded, **inside its transaction, only on success**. An empty load keeps the old value.
- The bronze load flips to `0` the rows already confirmed by **all** the gold tables that read them:
  `UPDATE BRONZE.<TABLE> SET IS_LAST_INSERT_TO_BRONZE_IND = 0 WHERE IS_LAST_INSERT_TO_BRONZE_IND = 1 AND LOAD_TO_BRONZE_TS <= (SELECT MIN(MAX_CONFIRMED_BRONZE_TS) FROM MNG.MNG_BRONZE_GOLD_DELTA WHERE BRONZE_TABLE_NAME = '<table>')`
- A NULL watermark → nothing is flipped. First deployment: seed it by joining bronze to gold on the logical key.

## After every bronze load: the gate

`Duplicates` on the staging table before the merge; `Empty_Table` on the bronze table after (`nogamy-qa-checks`). Fail → the item stops, the window does not advance.

A source with fully identical rows can pass no key: `TARGET_TABLE_KEYS` stays NULL, the duplicates check is skipped for it, and it is recorded as an open question for the source owner. `Empty_Table` still runs.

## Before you finish

- [ ] load pattern written in `sources/<system>/<table>.md` (and in the config row, where the system uses config)
- [ ] re-running the same window gives the same bronze row count
- [ ] the window advances only after the gate passes
- [ ] a failed extract leaves bronze as it was

## Platform specifics

Skills are core and read-only in a project. Platform facts come from, in order:
1. `references/<platform>.md` in this folder, for each platform named in `_context/platform.md` §2 (shipped: `fabric.md`, `adf.md`, `airflow.md`).
2. `_context/platform.md` §10 → `nogamy-bronze-load`: what this project adds or overrides.
3. Neither exists → the table below is the question list: fill the answers in `_context/platform.md` §10 at setup (`nogamy-project-setup`), verified in the official docs (`nogamy-platform-watch`).

| Topic | This project |
|---|---|
| How data lands (copy step, bulk load, files, API) | ? |
| Where the ETL columns are filled (source query, the tool, a default) | ? |
| Merge syntax and its limits; NULL-safe comparison | ? |
| Safety overlap of the window; guard thresholds | ? |
| Type mapping per source engine (a table per source: source type → bronze type → what the query must cast) | `sources/<system>/README.md` |
| Errors seen while loading, with cause and fix | `nogamy-troubleshoot` |
