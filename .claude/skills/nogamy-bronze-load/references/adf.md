# nogamy-bronze-load — Azure Data Factory

Read when `_context/platform.md` §2 names Azure Data Factory (or Synapse pipelines, where noted). Answers the "Platform specifics" topics of `SKILL.md` for ADF moving data into the project's database. A project override goes in `_context/platform.md` §10 → `nogamy-bronze-load`.

ADF moves data; the merge runs in the database. Merge syntax is the target database's (`nogamy-write-sql`, `nogamy-db-objects` and their reference for that database), not ADF's.
Pipeline structure (master, child, ForEach, gate): `nogamy-build-pipeline` → `references/adf.md`.

## Platform specifics

| Topic | Azure Data Factory |
|---|---|
| How data lands | Copy activity: source query → `PRE_BRONZE.PRE_<bronze table>`, emptied first by the sink's `preCopyScript` (`TRUNCATE TABLE …`, run once per copy). Then a Script or Stored Procedure activity runs `BRONZE.SP_LOAD_BRONZE_<SYSTEM>` (merge by key) |
| Where the ETL columns are filled | in the source query. Not in the Copy's `additionalColumns` (verify: their data type; Learn states String only for `$$FILEPATH`) |
| Merge syntax and limits; NULL-safe comparison | the target database's (see above) |
| Safety overlap; guard thresholds | the method defaults (`merge-load.md`): from = last `to` − overlap, to = load start (UTC); guard `> 10` and `> 5%` |
| Type mapping per source engine | Copy maps through its interim types; per source in `sources/<system>/README.md`; Oracle: `oracle-source.md` |
| Errors seen while loading | `nogamy-troubleshoot` → `references/adf.md` |

## Copy sink options we do not use for bronze

- `writeBehavior: upsert` (SQL sinks): it skips the guard, the soft delete and the change check. The merge procedure does them.
- `sqlWriterStoredProcedureName`: it runs per batch, not once.
- `tableOption: autoCreate`: tables come from migrations (`nogamy-db-objects`).

## Window and watermark

Our window comes from the config row (`nogamy-bronze-load`). Microsoft's watermark tutorial has the same shape:
1. Lookup the old value (config row: `LAST_TO_DELTA`).
2. Fix the new value before copying (the load start time, UTC).
3. Copy rows with `> old` and `<= new` in the source query.
4. Update the stored value after success.

Ours adds: the special-dates override, and step 4 only after the gate passed (`Update_Config_Window`).
Row counts for the checks: the Copy output `rowsRead` and `rowsCopied` (`@activity('<Copy>').output.rowsCopied`).
Other options Learn offers: SQL Change Tracking; `LastModifiedDate` or time-partitioned paths for files.

## Self-hosted integration runtime (on-premises sources)

| Fact | Value |
|---|---|
| Machine | Windows 10/11 or Windows Server 2016–2025, 64-bit, .NET Framework 4.7.2+. Not a domain controller |
| Per machine | one self-hosted IR |
| High availability | up to 4 nodes, registered with the same key |
| Network | outbound only, HTTPS 443; 8060 only between nodes |
| Credentials | encrypted on the node, unless the linked service reads Key Vault (preferred) |
| Shared between factories | yes, as a linked IR, same tenant. Not in Synapse |
| Across environments | the same IR name and type in DEV, TEST and PROD |
| Parquet, ORC, Avro on the node | needs a Java runtime (JRE 11+) |

- Install, register and give network access: a person (admin). Never the AI.
- Its name goes in `_context/platform.md` §2; its machine and owner in `PROJECT.md` → Environments.

## Config and the gate

- The pipelines read config rows with `IS_ACTIVE = 1`. Nothing source-specific in the pipeline JSON.
- Gate after the Copy: `ExecutePipeline` → `GPL_DQA` (`Duplicates` on `PRE_BRONZE`) before the merge; `Empty_Table` on bronze after.
- Window advance and the reset of `IS_MASS_DELETE_APPROVED`: only after the gate passed.

## Sources

- https://learn.microsoft.com/en-us/azure/data-factory/copy-activity-overview
- https://learn.microsoft.com/en-us/azure/data-factory/copy-activity-monitoring
- https://learn.microsoft.com/en-us/azure/data-factory/connector-sql-server
- https://learn.microsoft.com/en-us/azure/data-factory/tutorial-incremental-copy-overview
- https://learn.microsoft.com/en-us/azure/data-factory/tutorial-incremental-copy-portal
- https://learn.microsoft.com/en-us/azure/data-factory/create-self-hosted-integration-runtime
- https://learn.microsoft.com/en-us/azure/data-factory/concepts-integration-runtime
- https://learn.microsoft.com/en-us/azure/data-factory/self-hosted-integration-runtime-troubleshoot-guide
