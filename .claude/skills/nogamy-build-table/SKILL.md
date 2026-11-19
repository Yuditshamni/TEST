---
name: nogamy-build-table
description: Build a dimension or fact end to end from an approved STT — gold table, silver view(s), silver staging, load procedure, -99 row, migration, data checks and column descriptions. Use when an stt/<domain>/<table>.md has status approved and the table does not exist yet or changes.
---

# Build a table from the STT

Prerequisites (iron rules): STT `status: approved` · its dimensions already built (facts last) · PK / FK / index policy known. Missing → stop and say what is missing.

## Inputs

- `stt/<domain>/<table>.md`: columns, sources, transformation, load pattern, grain, `description_he`, `synonyms_he`, `pii`
- `sources/<system>/<table>.md`: source columns and types
- `_context/business-rules.md`, `_context/glossary.md`
- what exists in DEV (structure only)

## Outputs (one file each)

Folders as in `nogamy-db-objects` (a platform reference may set another root, e.g. `references/fabric.md` there). Platform specifics for this skill: `references/<platform>.md` (shipped: `fabric.md`, `sqlserver.md`).

| # | File | Content | When |
|---|---|---|---|
| 1 | `db/GOLD/Tables/<PROJECT>_<TABLE>.sql` | the gold table, with the ETL columns of its load pattern | always |
| 2 | `db/SILVER/Views/V_<PROJECT>_<TABLE>.sql` | all silver logic; final column list as the gold table | always; split into `_STEP…` views only where readability needs it (`nogamy-db-objects`) |
| 3 | `db/SILVER/Tables/SILVER_<PROJECT>_<TABLE>.sql` | silver staging: freezes this load | always |
| 4 | `db/SILVER/Procedures/SP_<PROJECT>_<TABLE>.sql` | load procedure, pattern from the STT (`nogamy-db-objects`) | always |
| 5 | `scripts/migrations/NNNN_<what>.sql` | brings an environment to files 1–4 | always |
| 6 | `scripts/seed/…` | watermark row for each bronze → gold pair | delta loads from an accumulating bronze |
| 7 | `qa/data/<GOLD TABLE>.sql` | checks (`nogamy-qa-checks`) | always |
| 8 | `stt/<domain>/<table>.md` | set `built: <date>, <branch>` | always |

The smallest case (a dimension, full reload): `GOLD.SALES_DIM_REGION`, `SILVER.V_SALES_DIM_REGION`, `SILVER.SILVER_SALES_DIM_REGION`, `SILVER.SP_SALES_DIM_REGION`, `qa/data/SALES_DIM_REGION.sql`, plus its migration.

A project that does not transform with SQL procedures (`_context/platform.md` §2) keeps the same contract in its own tool: logic readable in one place, a frozen staging step, an idempotent gold load, the same checks.

## Order

1. Plan: file list + load pattern + how many views and why + checks + who runs what → approval (`nogamy-plan-and-explain`).
2. Write the files in the table's order: gold table → view(s) → staging → procedure → migration → seed → checks.
3. `nogamy-dev-workflow` from "Run in DEV": apply, run twice, checks, commit, compare repo with DEV, hand over.
4. Descriptions: `description_he` and `synonyms_he` from the STT go to the BI model (`nogamy-semantic-model`). They are part of "done".

## Rules

- Column order exactly as the STT. Names per `nogamy-naming` (UPPERCASE), even if the STT writes them differently. Any other mismatch STT ↔ code is a mine: ask.
- `pii: yes` columns: built, but never read by the AI; listed in `_context/access-rules.md` for row- or column-level security.
- Load pattern per table, from the STT. Not stated → ask, do not default.
- Fact: grain stated in the header comment; `FACT_KEY` defined; every dimension key resolved or `-99`.
- One entity at a time. The next entity starts after this one's checks pass twice.
