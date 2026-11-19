# nogamy-build-table — SQL Server / Azure SQL Database

Read when `_context/platform.md` §2 names SQL Server or Azure SQL Database. The contract and the files in `SKILL.md` are the same; this file says what T-SQL adds and how DEV is run.

## Outputs on SQL Server

Files 1–8 as in `SKILL.md`, under `db/` (no other root). Procedures in `db/SILVER/Procedures/`.

| File | SQL Server detail |
|---|---|
| 1 gold table | types per `nogamy-db-objects` → `references/sqlserver.md`: `nvarchar` for Hebrew text, `datetime2` for ETL dates. Constraints and indexes only as the project's PK / FK policy says (`_context/architecture.md`); a large fact: a clustered columnstore index if the policy allows indexes |
| 2 view(s) | `CREATE VIEW` alone in its batch; no `ORDER BY` |
| 4 procedure | the frame in `nogamy-db-objects` → `references/sqlserver-load-procedure-templates.md` |
| 5 migration | guards in T-SQL (`nogamy-db-objects` → `references/sqlserver.md`); `GO` between batches: table, view, staging, procedure |
| `-99` row | text in Hebrew as `N'...'` |

## Running in DEV

At the level in `_context/platform.md` §7 (`nogamy-dev-workflow` → `references/sqlserver.md`). Below L2 each step is a run-sheet line.

1. Apply the migration: `python tools/run_migrations.py --profile dev --as-agent`.
2. Run the load twice, the checks after each: `sqlcmd -S <server> -d <database> -E -b -Q "EXEC SILVER.SP_<TABLE>"`, then `... -i qa/data/<GOLD TABLE>.sql` (**Azure SQL DB**: `-G` instead of `-E`).
3. Compare repo with DEV (`nogamy-dev-workflow` → `references/sqlserver.md` step 5).
4. The table's run order: `nogamy-build-pipeline`.

## Descriptions in the database (optional)

The descriptions go to the BI model (`SKILL.md` step 4). A project that also wants them in the database uses extended properties (`sys.sp_addextendedproperty` on the column, `sys.sp_updateextendedproperty` to change it; read with `sys.fn_listextendedproperty`), in a migration, guarded by a lookup with `sys.fn_listextendedproperty`. verify: the behaviour of `sp_addextendedproperty` when the property already exists.

## Sources

- https://learn.microsoft.com/en-us/sql/relational-databases/system-stored-procedures/sp-addextendedproperty-transact-sql
- https://learn.microsoft.com/en-us/sql/relational-databases/indexes/columnstore-indexes-overview
- https://learn.microsoft.com/en-us/sql/t-sql/statements/create-view-transact-sql
- https://learn.microsoft.com/en-us/sql/t-sql/queries/select-order-by-clause-transact-sql
- https://learn.microsoft.com/en-us/sql/t-sql/data-types/nchar-and-nvarchar-transact-sql
