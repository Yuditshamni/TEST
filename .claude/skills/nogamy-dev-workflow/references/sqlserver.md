# nogamy-dev-workflow — SQL Server / Azure SQL Database

Read when `_context/platform.md` §2 names SQL Server or Azure SQL Database. No pack is needed: the core's `tools/run_migrations.py` speaks T-SQL.

**Azure SQL DB** marks where Azure SQL Database differs from SQL Server on-premises.

## Access level

No default for this platform: the level is whatever `_context/platform.md` §7 says (L0 until set). The AI works only in the DEV database, as the AI identity (`PROJECT.md` → Environments). Its profile in `_private/db-profiles.json` has `"environment": "DEV"` and `"agent": true`; no TEST or PROD profile is ever marked `agent`.

## 2. Branch and files

| What | Where |
|---|---|
| database objects | `db/<SCHEMA>/<Tables\|Views\|Procedures\|Functions>/<OBJECT>.sql` + the next migration in `scripts/migrations/` (`nogamy-db-objects`) |
| SQL project, if the project uses one | `db/` holds the `.sqlproj` and the same object files (`_context/platform.md` §6) |
| ETL items | the ETL tool's folder under `etl/` (`nogamy-build-pipeline`) |
| checks | `qa/data/<GOLD TABLE>.sql` |

## 3. Run in DEV

| What | How |
|---|---|
| any database change | the migration: `python tools/run_migrations.py --profile dev --as-agent` (L2+). Never the object file directly. A migration with `DROP`: the developer runs it without `--as-agent` |
| what is pending | `python tools/run_migrations.py --profile dev --dry-run` |
| L0 / L1 | `python tools/run_migrations.py --platform sqlserver --run-sheet --from <n>` → a person runs it in SSMS, VS Code or `sqlcmd` and pastes the log rows back |
| a load procedure, a check | `sqlcmd -S <server> -d <database> -E -b -Q "EXEC SILVER.SP_<TABLE>"` · `... -i qa/data/<table>.sql`. **Azure SQL DB**: `-G` (Microsoft Entra ID) instead of `-E` |
| SQL project build (if used) | `dotnet build db/<name>.sqlproj` → `.dacpac` in `bin/Debug`; a build error is a broken reference |

Try-outs: `#temp` tables (session). A try-out that must outlive the session: `TRY_` (`nogamy-db-objects`).

## 5. Compare repo with DEV

No core drift tool for this platform yet. Two checks:
1. Names: objects in DEV vs files in `db/`. Read-only:
   `SELECT s.name AS SCHEMA_NAME, o.name AS OBJECT_NAME, o.type_desc FROM sys.objects AS o JOIN sys.schemas AS s ON s.schema_id = o.schema_id WHERE o.is_ms_shipped = 0 AND o.type IN ('U','V','P','FN','IF','TF') ORDER BY 1, 2;`
   An object without a file, or a file without an object → report it.
2. Definitions (with a SQL project): `SqlPackage /Action:DeployReport /SourceFile:<dacpac> /TargetConnectionString:"<DEV>" /OutputPath:<scratch>.xml`. An empty list = the repo and DEV agree. Without a project: `SqlPackage /Action:Extract /p:ExtractTarget=SchemaObjectType` to a scratch folder outside the repo, then compare by hand.

## Platform specifics — answers

| Topic | SQL Server / Azure SQL Database |
|---|---|
| Access level | `_context/platform.md` §7 (no platform default) |
| Folder layout | `db/<SCHEMA>/<Type>/<OBJECT>.sql`; ETL per its tool under `etl/` |
| Run a query / a `.sql` file in DEV | `sqlcmd -S <server> -d <database> -E -b -Q "<sql>"` or `-i <file>.sql`; **Azure SQL DB** `-G` |
| Apply migrations in DEV | `tools/run_migrations.py --profile dev --as-agent` |
| Publish an ETL item to DEV | per ETL tool (`_context/platform.md` §10 → `nogamy-build-pipeline`); SQL Agent jobs: a migration-like script, run by a person |
| Run an ETL item and read its steps | SQL Agent (on-prem): `EXEC msdb.dbo.sp_start_job @job_name = N'<job>'`, then `msdb.dbo.sysjobhistory` (`run_status`: 0 failed, 1 succeeded, 4 in progress; one row per step with `message`). **Azure SQL DB**: no SQL Agent; elastic jobs or the ETL tool |
| Compare repo with DEV | above |
| By hand in the UI | logins, users and grants (a person, `scripts/grants/`); **Azure SQL DB**: the firewall rule for the client |

## Sources

- https://learn.microsoft.com/en-us/sql/tools/sqlcmd/sqlcmd-utility
- https://learn.microsoft.com/en-us/sql/tools/sql-database-projects/sql-database-projects
- https://learn.microsoft.com/en-us/sql/tools/sqlpackage/sqlpackage-deploy-drift-report
- https://learn.microsoft.com/en-us/sql/tools/sqlpackage/sqlpackage-extract
- https://learn.microsoft.com/en-us/sql/relational-databases/system-stored-procedures/sp-start-job-transact-sql
- https://learn.microsoft.com/en-us/sql/relational-databases/system-tables/dbo-sysjobhistory-transact-sql
- https://learn.microsoft.com/en-us/sql/relational-databases/system-catalog-views/sys-objects-transact-sql
- https://learn.microsoft.com/en-us/azure/azure-sql/database/elastic-jobs-overview
- https://learn.microsoft.com/en-us/azure/azure-sql/database/transact-sql-tsql-differences-sql-server
- https://learn.microsoft.com/en-us/azure/azure-sql/database/troubleshoot-common-errors-issues
