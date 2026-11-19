# nogamy-db-objects — SQL Server / Azure SQL Database

Read when `_context/platform.md` §2 names SQL Server or Azure SQL Database. Answers the "Platform specifics" topics of `SKILL.md`. A project override goes in `_context/platform.md` §10 → `nogamy-db-objects`. Dialect details: `nogamy-write-sql` → `references/sqlserver.md`. Procedure frame: `sqlserver-load-procedure-templates.md`.

**Azure SQL DB** marks where Azure SQL Database differs from SQL Server on-premises.

## Where

```
db/<SCHEMA>/<Tables|Views|Procedures|Functions>/<OBJECT>.sql
```

- The core default: plain files + numbered migrations (`scripts/README.md`). No pack is needed.
- Object files hold `CREATE` only. `CREATE OR ALTER` and the guards are for migrations.
- A project that keeps an SDK-style SQL project (`.sqlproj`, `Microsoft.Build.Sql`) puts it in `db/` and records it in `_context/platform.md` §6. Still one object, one file. How it deploys: `nogamy-deploy` → `references/sqlserver.md`.

## Migration guards in T-SQL

| Change | Guard |
|---|---|
| schema | `IF SCHEMA_ID(N'GOLD') IS NULL EXEC(N'CREATE SCHEMA GOLD');` (`CREATE SCHEMA` must be alone in its batch) |
| table | `IF OBJECT_ID(N'GOLD.SALES_DIM_CUSTOMER', N'U') IS NULL CREATE TABLE ...` |
| view, procedure, function | `CREATE OR ALTER ...` (SQL Server 2016 SP1+, Azure SQL DB), first statement of its batch: `GO` before it |
| column | `IF NOT EXISTS (SELECT 1 FROM sys.columns WHERE object_id = OBJECT_ID(N'GOLD.SALES_DIM_CUSTOMER') AND name = N'SEGMENT_NAME') ALTER TABLE ... ADD ...` |
| drop | `DROP TABLE IF EXISTS ...` / `DROP VIEW IF EXISTS ...` (SQL Server 2016+). A drop is run by a person |

`tools/run_migrations.py` splits a file on `GO` lines and sends each batch.

## Platform specifics

| Topic | SQL Server / Azure SQL Database |
|---|---|
| Folder root and folder names | above; procedures in `Procedures/` |
| Types | `nvarchar(n)` for business text in Hebrew (or `varchar` + a `_UTF8` collation, 2019+); `varchar(n)` for ASCII codes; `int`, `bigint`, `decimal(p,s)`, `date`, `datetime2(n)`, `bit`. Not `datetime`, `text`, `ntext`, `image` |
| Constraints and indexes | all enforced: `PRIMARY KEY`, `UNIQUE`, `FOREIGN KEY`, `CHECK`. Indexes: clustered, nonclustered, columnstore (large facts). PK / FK policy: ask once (`SKILL.md`). An enforced PK fails the load on a duplicate (error 2627) instead of a check finding it |
| `ALTER TABLE` | add a column; `ALTER COLUMN` (type, length, NULL); `DROP COLUMN`. A `NOT NULL` column with a constant default is added online on Enterprise edition (2012+); otherwise the table may be rewritten. Renames: `sp_rename` in a migration; Microsoft advises drop + re-create for views and procedures, and a renamed column is not updated in views that use `*` |
| Transactions, error handling, `MERGE` | supported. Frame: `BEGIN TRY` + `BEGIN TRANSACTION` + `SET XACT_ABORT ON`, `THROW` in `CATCH` (`sqlserver-load-procedure-templates.md`). `MERGE` ends with `;` |
| Temp tables | `#name`, session; dropped when the creating procedure ends. `##name`: global (on-prem: the whole instance; **Azure SQL DB**: the database). Not for try-outs that outlive the session: `TRY_` then |
| Does a truncate roll back inside a transaction? | **yes**, `TRUNCATE TABLE` rolls back. It also resets `IDENTITY` to the seed, needs `ALTER` on the table, and is refused on a table referenced by a `FOREIGN KEY`, in an indexed view, or system-versioned (temporal): use `DELETE` there |
| Backup of one table before a risky change | `SELECT <columns> INTO <dated copy> FROM <table>;` (no indexes, constraints or triggers are copied; name per `nogamy-naming`; a person drops it after the check). Whole database on-prem: a database snapshot (all editions of 2022; revert = the whole database, not a backup) or a full backup by the DBA. **Azure SQL DB**: no `BACKUP` / `RESTORE` statements; point-in-time restore creates a **new** database only (cannot overwrite), and a query cannot reach another database to copy a table back: the same-database copy is the table backup. `CREATE DATABASE ... AS COPY OF` copies a whole database |
| How migrations are applied to DEV | `python tools/run_migrations.py --profile <dev> [--as-agent]`, profile `"platform": "sqlserver"` (or `"azuresql"`) in `_private/db-profiles.json`. Default connection: Windows sign-in (`Trusted_Connection=yes`). **Azure SQL DB** has no Windows authentication: set `connection_string` with Microsoft Entra ID. verify: the `Authentication=` value the `mssql-python` driver accepts. L0: `--platform sqlserver --run-sheet` |
| A different transformation tool | a state-based SQL project (DACPAC): the object files are the project; migrations only for data moves, renames, backfills (`scripts/README.md`, `nogamy-deploy`) |
| Known traps | below |

## Known traps

- An FK from a fact to a dimension blocks the `TRUNCATE` of the full-reload dimension. Choose: no FK (base default), or a `DELETE` reload. Write the choice in `_context/architecture.md`.
- `DROP TABLE` and `CREATE TABLE` of the same table in one batch can fail: `GO` between them.
- The AI's load identity needs `ALTER` on staging and gold for `TRUNCATE`. Granted in `scripts/grants/`, by a person.
- Finding try-outs in DEV: `_` is a `LIKE` wildcard: `WHERE name LIKE N'TRY[_]%'`.

## Sources

- https://learn.microsoft.com/en-us/sql/t-sql/statements/truncate-table-transact-sql
- https://learn.microsoft.com/en-us/sql/t-sql/statements/create-procedure-transact-sql
- https://learn.microsoft.com/en-us/sql/t-sql/statements/create-view-transact-sql
- https://learn.microsoft.com/en-us/sql/t-sql/statements/create-schema-transact-sql
- https://learn.microsoft.com/en-us/sql/t-sql/statements/drop-table-transact-sql
- https://learn.microsoft.com/en-us/sql/t-sql/statements/drop-view-transact-sql
- https://learn.microsoft.com/en-us/sql/t-sql/statements/alter-table-transact-sql
- https://learn.microsoft.com/en-us/sql/relational-databases/system-stored-procedures/sp-rename-transact-sql
- https://learn.microsoft.com/en-us/sql/t-sql/statements/create-table-transact-sql
- https://learn.microsoft.com/en-us/sql/relational-databases/databases/tempdb-database
- https://learn.microsoft.com/en-us/sql/t-sql/statements/merge-transact-sql
- https://learn.microsoft.com/en-us/sql/t-sql/statements/set-xact-abort-transact-sql
- https://learn.microsoft.com/en-us/sql/t-sql/queries/select-into-clause-transact-sql
- https://learn.microsoft.com/en-us/sql/relational-databases/databases/database-snapshots-sql-server
- https://learn.microsoft.com/en-us/sql/sql-server/editions-and-components-of-sql-server-2022
- https://learn.microsoft.com/en-us/azure/azure-sql/database/recovery-using-backups
- https://learn.microsoft.com/en-us/azure/azure-sql/database/database-copy
- https://learn.microsoft.com/en-us/azure/azure-sql/database/transact-sql-tsql-differences-sql-server
- https://learn.microsoft.com/en-us/sql/relational-databases/indexes/columnstore-indexes-overview
- https://learn.microsoft.com/en-us/sql/t-sql/language-elements/like-transact-sql
- https://learn.microsoft.com/en-us/sql/tools/sql-database-projects/sql-database-projects
