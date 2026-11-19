---
name: nogamy-naming
description: The single source for every name in the project — schemas, tables, views, columns, procedures, ETL items, parameters, files, branches, temp tables — with the source of each rule (Nogamy base / project / client) and its status. Use before naming anything, and in every review.
---

# Naming

Every other skill links here. A name rule lives in one place only: this skill (core) or the project's naming table.
Source: **N** = Nogamy base (`standards/base_prompt.md`), **P** = project decision, **C** = the client's convention. Status: **decided** / **default** / **to confirm** (`_context/open-questions.md`).

**In a project this skill is read-only.** The project's choices (a `default` row set to `decided` or changed, a client rule with source **C**) are rows of the same shape in `PROJECT.md` → Project rules → Naming; there they win over a `default` here. A rule that is wrong for every project → `nogamy-feedback`.
At setup: walk the tables with the project lead and record each choice there. Names that exist only on one platform: `references/<platform>.md` (shipped: `fabric.md`, `sqlserver.md`).

## Rules above all names

| Rule | Source | Status |
|---|---|---|
| Same names in every environment. No `DEV` / `TEST` / `PROD` in any name or inside code. We deploy the same definitions | N | decided |
| References as `SCHEMA.OBJECT`. Never a database or server name inside code | N | decided |
| Words separated by `_`. No spaces, no non-English letters in identifiers | N | decided |
| One exact spelling per name, everywhere, also when the platform is not case sensitive | N | decided |
| Case of database identifiers: `UPPER_SNAKE_CASE` for schemas, tables, views, procedures and columns. Names from the STT are converted, even if the STT writes them in lowercase | N | default |
| Pick one convention and apply it everywhere; examples are examples | N | decided |

## Database

| Object | Pattern | Example | Source | Status |
|---|---|---|---|---|
| schemas | the layer | `PRE_BRONZE`, `BRONZE`, `SILVER`, `GOLD`, `MNG` (+ `SERVE` where the project has views for BI, + `QA` where the quality framework lives there) | N | default |
| layer prefix on table names | table name starts with its schema, **except GOLD** | `BRONZE.BRONZE_…`, `SILVER.SILVER_…`, `MNG.MNG_…` | N | default |
| project prefix | `<PROJECT>_` after the layer prefix, when several projects share one database. Without it, the project of a bronze table lives in `SOURCE_GROUP` of the config table | `SALES_` | P | to confirm |
| bronze table | `BRONZE.BRONZE_<SYSTEM>_<SOURCE_TABLE>` | `BRONZE.BRONZE_CRM_CUSTOMERS` | N | default |
| merge staging table | `PRE_` + the schema and name of the bronze table | `PRE_BRONZE.PRE_BRONZE_CRM_CUSTOMERS` | N | default |
| bronze merge procedure (one per source system) | `BRONZE.SP_LOAD_BRONZE_<SYSTEM>` | `BRONZE.SP_LOAD_BRONZE_CRM` | N | default |
| dimension / fact | `GOLD.<PROJECT>_DIM_<ENTITY>`, `GOLD.<PROJECT>_FACT_<SUBJECT>` | `GOLD.SALES_DIM_CUSTOMER` | N | default |
| silver view | `SILVER.V_<PROJECT>_<TABLE>` | `SILVER.V_SALES_DIM_CUSTOMER` | N | default |
| silver views when split (only the steps needed) | `…_STEP1_SOURCE` → `_STEP2_KEYS` → `_STEP3_NA` → `_STEP4_ETL` → `_FINAL_STEP` | `SILVER.V_SALES_FACT_ORDERS_STEP2_KEYS` | N | default |
| serve view (optional, on gold only) | `SERVE.V_<PROJECT>_<TABLE>` | `SERVE.V_SALES_FACT_ORDERS` | N | default |
| silver staging (every entity) | `SILVER.SILVER_<PROJECT>_<TABLE>` | `SILVER.SILVER_SALES_DIM_CUSTOMER` | N | default |
| load procedure (one per entity) | `SILVER.SP_<PROJECT>_<TABLE>` | `SILVER.SP_SALES_DIM_CUSTOMER` | N | default |
| config / watermark / migration log | `MNG.MNG_BRONZE_CONFIGURATION` (where a source uses config), `MNG.MNG_BRONZE_GOLD_DELTA` (delta loads), `MNG.MNG_MIGRATION_LOG` | | N + P | default |
| quality framework | `MNG.MNG_DQA_QUERY`, `MNG.MNG_DQA_RESULT`, `MNG.SP_DQA` (base). A platform pack may ship them as `QA.QA_DQA_QUERY`, `QA.QA_DQA_RESULT`, `QA.SP_DQA`: then those names hold | | N | to confirm |
| temp table | the platform's session temp table, named by purpose | `#CUSTOMER_CHANGES` | P | default |
| try-out that outlives a session | `TRY_` before the full name, every object of the try-out; never reaches the main branch (`nogamy-db-objects`) | `GOLD.TRY_SALES_DIM_CUSTOMER`, `SILVER.TRY_V_SALES_DIM_CUSTOMER` | N | decided |

## Columns

| Column | Pattern | Source | Status |
|---|---|---|---|
| all columns | `UPPER_SNAKE_CASE`; STT names converted | N | default |
| entity key | `KEY_<ENTITY>`: the dimension's key **and** the foreign key in every fact; same name everywhere; holds the business key value (no surrogate generator) | N | decided |
| role-playing key | `KEY_<ROLE>` joined to the dimension's key: `KEY_ORDER_DATE` → `KEY_DATE` | N | decided |
| fact logical key | `FACT_KEY` | N | decided |
| unknown member | key `-99` (`'-99'` for text keys) | N | decided |
| ETL columns | `ETL_INSERT_DATE`, `ETL_UPDATE_DATE`, `LOAD_TO_BRONZE_TS`, `IS_LAST_INSERT_TO_BRONZE_IND` | N | decided |
| soft delete | `DELETED_DATE`, NULL unless the row left the source; carried to gold | P | to confirm |
| flags | `IS_<STATE>_IND`, `IS_CURRENT_FLAG`; SCD2 `VALID_FROM`, `VALID_TO` | N | decided |
| last-version flag | `IS_LAST_UPDATE_IND` on every gold table (always `1` outside match-by-key loads) | N | decided |
| framework tables | base column names, in `UPPER_SNAKE_CASE`: `SOURCE_SYSTEM`, `BRONZE_TABLE_NAME`, `GROUP_NAME` … | N | decided |

## ETL and orchestration items

Words in these names follow the tool's own habit (often `Pascal_Snake`); the roles are fixed.

| Object | Pattern | Example | Source |
|---|---|---|---|
| pipeline / job | `PL_<Action>_<Domain>_<Layer>` | `PL_Run_Sales_Gold` | N |
| shared, generic item | `GPL_<Name>` | `GPL_DQA` | N |
| roles | `_Master` (reads config, loops), `_To_Bronze` (one source table), `_Daily_Run` (schedule), `PL_Run_<Domain>_Bronze`, `PL_Run_<Domain>_Gold` | | N |
| parameter / variable | `P_<name>` / `V_<name>` | `P_Target_Table_Name`, `V_From_Date` | N |
| step / activity | a procedure step = the procedure's name; a lookup = what it fetches; `Set_<variable>`; a barrier wait `Finish Dims` / `Finish Facts` | `Get_Active_Sources_From_Config` | N |
| quality group | `<Domain>_GOLD_Dims`, `<Domain>_GOLD_Facts`, `<Domain>_Others` | `Sales_GOLD_Dims` | N |
| folders | `etl/<project>/00_orchestration`, `01_bronze`, `02_silver`, `03_gold`, `04_qa`; shared: `etl/_shared/` | | P |

## Repo

| Item | Pattern | Example |
|---|---|---|
| database object file | named exactly as the object: `db/<SCHEMA>/<Tables\|Views\|Procedures\|Functions>/<OBJECT>.sql` | `db/GOLD/Tables/SALES_DIM_CUSTOMER.sql` |
| migration | `scripts/migrations/NNNN_<what>.sql`, next free number, never renumbered after merge | `0012_add_sales_dim_customer.sql` |
| per-table checks | `qa/data/<GOLD TABLE>.sql` | `qa/data/SALES_DIM_CUSTOMER.sql` |
| end-to-end QA | `qa/data/QA_<PROJECT>_END_TO_END.sql` | |
| test document of a deploy | `qa/deploy/<branch topic>.md` | `qa/deploy/dim-customer.md` |
| STT / source spec | `stt/<domain>/<GOLD TABLE>.md`, `sources/<system>/<SOURCE_TABLE>.md` | `stt/sales/SALES_DIM_CUSTOMER.md` |
| project skill / agent | `.claude/skills/<project-id>-<what>/`, `.claude/agents/<project-id>-<what>.md`, registered in `PROJECT.md`; never `nogamy-` | `sales-dwh-month-close` |
| branch | `feature/<what>`, `stt/<what>`, `context/<topic>` | `feature/dim-customer` |
| commit | `<scope>: <what> — <why>` | `stt: add CLOSED_DATE — requested by the client` |

## The client's conventions

Whether the client has conventions to adopt is tracked in `_context/open-questions.md`. When the client has rules to adopt, they enter the project's naming table (`PROJECT.md` → Project rules → Naming) with source **C**, and the default they replace is named there, not kept beside it.
