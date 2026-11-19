# nogamy-bronze-load — Microsoft Fabric

Read when `_context/platform.md` §2 names Fabric. Answers the "Platform specifics" topics of `SKILL.md` for Fabric Data Factory into the Fabric Warehouse. A project override goes in `_context/platform.md` §10 → `nogamy-bronze-load`.

Needs the Fabric pack (`tools/fabric/`, `tools/migrate/`, `PROJECT.md` → `Packs: fabric`). Missing → run `nogamy-add-pack` first.

Detail files: `fabric-merge-load.md` (merge on the Warehouse), `fabric-oracle-gateway.md` (Oracle through the gateway).

## Framework objects

The pack ships them under `fabric/data/WH_DWH.Warehouse/`: `MNG.MNG_BRONZE_CONFIGURATION`, `MNG.MNG_BRONZE_GOLD_DELTA`, `MNG.MNG_MIGRATION_LOG`, and the quality framework `QA.QA_DQA_QUERY`, `QA.QA_DQA_RESULT`, `QA.SP_DQA` (`nogamy-qa-checks` → `references/fabric.md`). Check they are on the main branch and applied in DEV before the first source.

## Platform specifics

| Topic | Fabric |
|---|---|
| How data lands | a Copy activity lands in `PRE_BRONZE.PRE_<bronze table>` (truncated first), then `BRONZE.SP_LOAD_BRONZE_<SYSTEM>` merges by key. Straight to `BRONZE` only for a `FULL` table with no key yet: truncate and reload |
| Where the ETL columns are filled | in the source query (the child pipeline wraps the config query: `oracle-source.md`), never in the Copy's `additionalColumns` (always a string) |
| Merge syntax and limits; NULL-safe comparison | `MERGE` with `IS [NOT] DISTINCT FROM`; no explicit transaction around flag + merge (`fabric-merge-load.md`) |
| Safety overlap; guard thresholds | window `V_From_Date = LAST_TO_DELTA - 1 day`, `V_To_Date` = when the load started (UTC). Guard: `MISSING > 10` and `> 5%` of active rows |
| Type mapping per source engine | Oracle: `fabric-oracle-gateway.md`; others in `sources/<system>/README.md` |
| Errors seen while loading | `fabric-oracle-gateway.md`; then `nogamy-troubleshoot` |

## Config and the gate in the pipelines

- Pipelines read config rows with `IS_ACTIVE = 1`; nothing source-specific in the pipeline JSON.
- The gate is `QA.SP_DQA`: `Duplicates` on the `PRE_BRONZE` table the Copy filled, before the `MERGE`; `Empty_Table` on the bronze table after. A row with `TARGET_TABLE_KEYS` NULL: `PL_<Source>_To_Bronze` skips `Duplicates` for it.
- Window advance and the reset of `IS_MASS_DELETE_APPROVED`: the `Update_Config_Window` activity, only after the gate passed.

## Not used on Fabric (Snowflake / Blob methodology only)

External stages, `COPY INTO` from a stage, file formats, `VARIANT` + `FLATTEN`, Blob folder conventions, `_To_Blob` pipelines (`standards/BRONZE_Snowflake_Blob_Methodology.md`). A JSON source lands as a table, or as a string parsed in T-SQL.
