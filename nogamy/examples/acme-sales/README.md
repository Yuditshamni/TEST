# Worked example — Acme sales, one dimension end to end

Acme is an invented company. All data here is invented: no real people, no client.

What it shows: one entity, `GOLD.SALES_DIM_CUSTOMER`, built the Nogamy way, from the source description to the checks.
Every file is the finished version of a Nogamy artifact. Open it to see what "done right" looks like.

Platform: SQL Server 2022 (T-SQL). The project facts it assumes: `_context-notes.md`.

## The flow

```
ERP CUSTOMERS ──(bronze load, FULL)──► BRONZE.BRONZE_ERP_CUSTOMERS
  ──► SILVER.V_SALES_DIM_CUSTOMER_STEP1_SOURCE   (bronze filter, rank per customer)
  ──► SILVER.V_SALES_DIM_CUSTOMER_FINAL_STEP     (one row per customer, STT rules, the -99 row)
  ──(SILVER.SP_SALES_DIM_CUSTOMER)──► SILVER.SILVER_SALES_DIM_CUSTOMER ──► GOLD.SALES_DIM_CUSTOMER
```

## Files

| File | What it demonstrates | Skill |
|---|---|---|
| `_context-notes.md` | the project facts a build relies on: platform, prefix, PK policy, load patterns, business rules, an open question, a logged deviation | `nogamy-project-memory`, `nogamy-method` |
| `sources/acme_erp/README.md` | a source system: access, load pattern and why, deletes, findings with evidence (counts, never rows) | `nogamy-specs` |
| `sources/acme_erp/CUSTOMERS.md` | a source table profile: types, null %, distinct counts, `meaning_he`, `pii` on every column | `nogamy-specs`, `nogamy-explore-data` |
| `stt/sales/SALES_DIM_CUSTOMER.md` | an approved STT: grain, load, every column with source, transformation in words, `description_he`, `synonyms_he`, `pii` | `nogamy-specs` |
| `db/BRONZE/Tables/BRONZE_ERP_CUSTOMERS.sql` | a bronze table: the source as is + the four ETL columns, incl. `IS_LAST_INSERT_TO_BRONZE_IND` | `nogamy-bronze-load` |
| `db/SILVER/Views/V_SALES_DIM_CUSTOMER_STEP1_SOURCE.sql` | silver view 1: the bronze filter, the rank that BR-001 needs; header says why two views | `nogamy-db-objects` |
| `db/SILVER/Views/V_SALES_DIM_CUSTOMER_FINAL_STEP.sql` | silver view 2: one row per key, the STT transformations, the `-99` row by `UNION ALL` | `nogamy-db-objects` |
| `db/SILVER/Tables/SILVER_SALES_DIM_CUSTOMER.sql` | silver staging: the gold columns without `ETL_UPDATE_DATE` | `nogamy-db-objects` |
| `db/GOLD/Tables/SALES_DIM_CUSTOMER.sql` | a gold dimension: `KEY_CUSTOMER`, STT column order, the standard ETL columns | `nogamy-build-table` |
| `db/SILVER/Procedures/SP_SALES_DIM_CUSTOMER.sql` | the load procedure, full reload: one transaction, `TRY` / `CATCH`, `THROW`, returns `SILVER_ROWS` and `GOLD_ROWS`, idempotent | `nogamy-db-objects` |
| `db/MNG/Tables/MNG_MIGRATION_LOG.sql` | the migration log, as an object file | `nogamy-db-objects` |
| `db/DEV_MAP.md` | the generated development map: no dependency on another entity | `nogamy-db-objects` |
| `scripts/migrations/0001_create_migration_log.sql` | migration 0001: the `MNG` schema and the log, pasted from `--print-log-ddl` | `nogamy-db-objects` |
| `scripts/migrations/0002_create_layer_schemas.sql` | guarded `CREATE SCHEMA` (`EXEC`, alone in its batch) | `nogamy-db-objects` |
| `scripts/migrations/0003_add_bronze_erp_customers.sql` | a guarded table, the same definition as its `db/` file | `nogamy-db-objects` |
| `scripts/migrations/0004_add_sales_dim_customer.sql` | one migration for one entity: tables guarded, views and procedure `CREATE OR ALTER`, `GO` between batches | `nogamy-build-table` |
| `scripts/migrations/0005_insert_example_bronze_rows.sql` | eight invented bronze rows, inserted only if missing (example only, see `_context-notes.md`) | `nogamy-qa-checks` |
| `qa/data/SALES_DIM_CUSTOMER.sql` | per-table checks: one row per check, `RESULT` = `PASS` / `FAIL`, rules that hold on any data | `nogamy-qa-checks` |
| `qa/golden/sales.md` | two golden questions in the users' words, with proof SQL | `nogamy-qa-checks` |

## What the test data makes visible

| Bronze rows | What happens | Rule |
|---|---|---|
| C-1005 twice (moved branch) | one gold row, the newer one | BR-001 |
| C-1003 NULL city, C-1004 empty city | both "לא ידוע" | BR-002 |
| C-1006 segment `XX` | "לא ידוע" | BR-003 |
| none | the `-99` row comes from the view | `nogamy-db-objects` |

8 bronze rows → 7 customers → 8 gold rows (7 + `-99`).

## How CI runs it

Core CI runs this folder on an empty SQL Server 2022 container:

1. Apply the migrations with `tools/run_migrations.py`, its migration folder pointed at `nogamy/examples/acme-sales/scripts/migrations` (platform `sqlserver`). `0001`–`0005` run in order; the log gets five rows with `IS_EXECUTED = 1`.
2. Apply them again: nothing pending (safe twice).
3. `EXEC SILVER.SP_SALES_DIM_CUSTOMER;` → one row: `SILVER_ROWS = 8`, `GOLD_ROWS = 8`.
4. Run `qa/data/SALES_DIM_CUSTOMER.sql`: 7 rows, every `RESULT` = `PASS`.
5. Run the procedure again, then the checks again: the same counts, all `PASS` (idempotent).

Offline, with no database: `python -c "import sys; sys.path.insert(0, 'tools'); import run_migrations as rm; from pathlib import Path; rm.FOLDER = Path('nogamy/examples/acme-sales/scripts/migrations'); print(rm.check_files())"` prints `[]`.
The map: `tools/dev_map.py` with its `DB` set to this `db/` folder.

## In a real project

The same files sit at the repo root (`sources/`, `stt/`, `db/`, `scripts/`, `qa/`), the facts in `PROJECT.md` and `_context/`, and bronze is filled by the bronze load, never by a migration.
