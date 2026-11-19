# nogamy-write-sql — SQL Server / Azure SQL Database

Read when `_context/platform.md` §2 names SQL Server or Azure SQL Database. Answers the "Platform specifics" topics of `SKILL.md` for T-SQL. A project override goes in `_context/platform.md` §10 → `nogamy-write-sql`.

**Azure SQL DB** marks where Azure SQL Database differs from SQL Server on-premises (or on a VM). No mark = the same on both.

## Platform specifics

| Topic | SQL Server / Azure SQL Database |
|---|---|
| Dialect and version | T-SQL. Record the version (`SELECT @@VERSION`) and the database compatibility level (`sys.databases.compatibility_level`) in `_context/platform.md` §2: a feature can need both. Defaults: SQL Server 2019 = 150, 2022 = 160, 2025 = 170. **Azure SQL DB**: always the current engine; new databases default to 170 |
| Case sensitivity: names · data · `LIKE` | set by the collation, per database (and per column). Usual default is **case insensitive** (`_CI_`): `'A' = 'a'`, also in `LIKE`. On-prem default comes from the OS locale at setup (US English: `SQL_Latin1_General_CP1_CI_AS`). **Azure SQL DB**: default `SQL_Latin1_General_CP1_CI_AS`; the catalog collation (object names) is fixed at creation. Read it: `SELECT DATABASEPROPERTYEX(DB_NAME(), 'Collation')` |
| Types to use · types that do not exist | text: `nvarchar(n)` for Hebrew or any non-Latin text (or `varchar` with a `_UTF8` collation, SQL Server 2019+ and Azure SQL DB); `varchar(n)` only for codes known to be ASCII. Numbers `int`, `bigint`, `decimal(p,s)`; dates `date`, `datetime2(0..7)`, `datetimeoffset` when the offset must be kept; flag `bit`. Do not use: `datetime` for new work ("avoid", Microsoft), `text` / `ntext` / `image` (to be removed; use `(n)varchar(max)`, `varbinary(max)`) |
| Row limiting | `TOP (n)`, not `LIMIT`. `OFFSET ... FETCH` for paging (needs `ORDER BY`) |
| String functions | `LEN` (ignores trailing spaces) vs `DATALENGTH` (bytes). `CONCAT`, `CONCAT_WS`, `TRIM`, `STRING_AGG` (all SQL Server 2017+). `TRIM(LEADING/TRAILING …)` needs 2022 + compatibility 160. `GREATEST` / `LEAST`: 2022+. `STRING_AGG` with `varchar` input cannot take an `nvarchar` separator. Unicode literals need `N'...'` |
| Date functions and time-zone conversion | `DATEADD`, `DATEDIFF`, `EOMONTH`, `CAST(x AS date)`; `DATETRUNC` only SQL Server 2022+ and Azure SQL DB. Now in UTC: `SYSUTCDATETIME()`. Convert: `x AT TIME ZONE 'UTC' AT TIME ZONE 'Israel Standard Time'` (2016+; Windows zone names, list in `sys.time_zone_info`; DST handled). `AT TIME ZONE` is nondeterministic |
| NULL-safe comparison | `IS [NOT] DISTINCT FROM`: SQL Server 2022+ and Azure SQL DB only. Older: `(a = b OR (a IS NULL AND b IS NULL))` |
| `MERGE`, transactions, error handling | `MERGE` must end with `;` (error 10713); errors if one target row matches more than one source row; `HOLDLOCK` against concurrent unique-key violations; count with `OUTPUT $action`. Plain `UPDATE` + `INSERT` (or delete + insert) is Microsoft's advice when one table is simply updated from another. Transactions with `BEGIN TRY / CATCH`, `THROW` (the statement before `THROW` ends with `;`), `SET XACT_ABORT ON` to roll back the whole transaction on a run-time error |
| Temp tables | `#name`: the session; created in a procedure → dropped when it ends. `##name`: global; on-prem visible to the whole instance, **Azure SQL DB**: scoped to the database. Temp tables live in `tempdb` with the instance collation (on-prem): a comparison with a user table can fail on a collation conflict: add a `COLLATE` clause (e.g. `COLLATE DATABASE_DEFAULT`). Local temp name: max 116 characters |
| Constraints and indexes | enforced: `PRIMARY KEY`, `UNIQUE`, `FOREIGN KEY`, `CHECK`, `NOT NULL`. Indexes: clustered, nonclustered, columnstore (Microsoft's standard for large fact tables). The PK / FK policy is the project's (`nogamy-db-objects`) |
| The system catalog | `INFORMATION_SCHEMA.COLUMNS`, `sys.objects`, `sys.columns`, `sys.indexes`, `sys.sql_modules` (definitions). Approximate row counts: `sys.dm_db_partition_stats` |
| Known traps | below |

## Known traps

- References: two-part `SCHEMA.OBJECT` only. **Azure SQL DB** refuses three- and four-part names to another database (only the current database and `tempdb`), and has no `USE`: one connection = one database.
- Case-insensitive by default: `'ABC' = 'abc'` is true, so case differences in codes stay hidden, and a `GROUP BY` merges them. Need exact: `COLLATE Latin1_General_100_BIN2` on the comparison, on purpose.
- Trailing spaces: `=` ignores them, `LIKE 'abc '` does not; `LEN` ignores them.
- `varchar` with a non-UTF-8 collation stores only the characters of its code page: Hebrew needs `nvarchar`, a Hebrew collation or `_UTF8`. A literal without `N` is converted to that code page first, also when the column is `nvarchar`.
- `GO` is not T-SQL: a batch separator for `sqlcmd`, SSMS and `tools/run_migrations.py`. `CREATE VIEW / PROCEDURE / FUNCTION` must be the first statement in its batch.
- `datetime` rounds to .000 / .003 / .007 seconds; `datetime2` does not. Compare a `date` column with a `datetime2` value only after an explicit `CAST`.
- `ORDER BY` in a view does not order the result.

## Running a query

- On-prem, Windows sign-in: `sqlcmd -S <server> -d <database> -E -b -i <file>.sql` (`-b` = exit code 1 on an error). One query: `-Q "<query>"`.
- **Azure SQL DB**: no Windows authentication; Microsoft Entra ID: `sqlcmd -S <server>.database.windows.net -d <database> -G -b -i <file>.sql`. A firewall rule must allow the client (error 40615).
- DEV only, as the AI identity, when `_context/platform.md` §7 allows it. The exact command goes in `PROJECT.md` → Agent tools.

## Debugging

`Invalid object name` (208) → schema, two-part name, the right database in the connection. Still unclear → search Microsoft Learn for the exact error text before guessing.

## Sources

- https://learn.microsoft.com/en-us/sql/t-sql/statements/alter-database-transact-sql-compatibility-level
- https://learn.microsoft.com/en-us/sql/relational-databases/collations/collation-and-unicode-support
- https://learn.microsoft.com/en-us/sql/t-sql/statements/create-database-transact-sql?view=azuresqldb-current
- https://learn.microsoft.com/en-us/sql/t-sql/data-types/nchar-and-nvarchar-transact-sql
- https://learn.microsoft.com/en-us/sql/t-sql/data-types/datetime-transact-sql
- https://learn.microsoft.com/en-us/sql/t-sql/data-types/ntext-text-and-image-transact-sql
- https://learn.microsoft.com/en-us/sql/t-sql/functions/string-agg-transact-sql
- https://learn.microsoft.com/en-us/sql/t-sql/functions/trim-transact-sql
- https://learn.microsoft.com/en-us/sql/t-sql/functions/concat-ws-transact-sql
- https://learn.microsoft.com/en-us/sql/t-sql/functions/logical-functions-greatest-transact-sql
- https://learn.microsoft.com/en-us/sql/t-sql/functions/len-transact-sql
- https://learn.microsoft.com/en-us/sql/t-sql/language-elements/like-transact-sql
- https://learn.microsoft.com/en-us/sql/t-sql/language-elements/string-comparison-assignment
- https://learn.microsoft.com/en-us/sql/t-sql/queries/select-order-by-clause-transact-sql
- https://learn.microsoft.com/en-us/sql/t-sql/functions/datetrunc-transact-sql
- https://learn.microsoft.com/en-us/sql/t-sql/queries/at-time-zone-transact-sql
- https://learn.microsoft.com/en-us/sql/t-sql/queries/is-distinct-from-transact-sql
- https://learn.microsoft.com/en-us/sql/t-sql/statements/merge-transact-sql
- https://learn.microsoft.com/en-us/sql/t-sql/language-elements/throw-transact-sql
- https://learn.microsoft.com/en-us/sql/t-sql/statements/set-xact-abort-transact-sql
- https://learn.microsoft.com/en-us/sql/t-sql/statements/create-table-transact-sql
- https://learn.microsoft.com/en-us/sql/relational-databases/databases/tempdb-database
- https://learn.microsoft.com/en-us/sql/relational-databases/indexes/columnstore-indexes-overview
- https://learn.microsoft.com/en-us/sql/relational-databases/system-dynamic-management-views/sys-dm-db-partition-stats-transact-sql
- https://learn.microsoft.com/en-us/azure/azure-sql/database/transact-sql-tsql-differences-sql-server
- https://learn.microsoft.com/en-us/sql/t-sql/language-elements/sql-server-utilities-statements-go
- https://learn.microsoft.com/en-us/sql/t-sql/statements/create-view-transact-sql
- https://learn.microsoft.com/en-us/sql/tools/sqlcmd/sqlcmd-utility
- https://learn.microsoft.com/en-us/azure/azure-sql/database/troubleshoot-common-errors-issues
