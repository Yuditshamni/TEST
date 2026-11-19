# nogamy-write-sql — Microsoft Fabric

Read when `_context/platform.md` §2 names Fabric. Answers the "Platform specifics" topics of `SKILL.md` for the Fabric Warehouse (T-SQL). A project override goes in `_context/platform.md` §10 → `nogamy-write-sql`.

## Platform specifics

| Topic | Fabric Warehouse |
|---|---|
| Dialect and version | T-SQL, Fabric Warehouse (a subset of SQL Server T-SQL) |
| Case sensitivity: names · data · `LIKE` | **case sensitive** everywhere (collation `Latin1_General_100_BIN2_UTF8`): `'A' <> 'a'`, object names must match exactly, `LIKE` is case sensitive. No `ILIKE` |
| Types to use · types that do not exist | `varchar` (UTF-8), `int`, `bigint`, `decimal(p,s)`, `date`, `datetime2(0..6)`, `bit`. No `nvarchar`, `datetime`, `money`, `text` |
| Row limiting | `TOP (n)`, not `LIMIT`. `OFFSET ... FETCH` for paging |
| String functions | `LEN`, `STRING_AGG`, `CONCAT_WS`, `TRIM` |
| Date functions and time-zone conversion | `DATEADD`, `DATEDIFF`, `DATETRUNC`, `EOMONTH`, `CAST(x AS date)`. Time is UTC; convert explicitly, e.g. for Israel time: `x AT TIME ZONE 'UTC' AT TIME ZONE 'Israel Standard Time'`. Now in UTC: `SYSUTCDATETIME()` |
| NULL-safe comparison | `IS [NOT] DISTINCT FROM` (used in the bronze merge, verified in DEV) |
| `MERGE`, transactions, error handling | supported: `MERGE`, `TRUNCATE`, transactions, `TRY/CATCH`, `THROW`, `IDENTITY` |
| Temp tables | `#name`, session scoped. Distributed form recommended: `CREATE TABLE #X (...) WITH (DISTRIBUTION = ROUND_ROBIN);`. No `##global` |
| Constraints and indexes | no user indexes. `PRIMARY KEY NONCLUSTERED ... NOT ENFORCED` only. Uniqueness is proven by checks |
| The system catalog | `sys.columns`, `sys.objects`, `INFORMATION_SCHEMA.COLUMNS`. One query cannot mix `sys.*` and user tables |
| Known traps | see below |

## Known traps

- References: two-part names only (`GOLD.SALES_DIM_CUSTOMER`). Never `WAREHOUSE.SCHEMA.OBJECT`.
- Performance without indexes: select few columns, filter early on the date column, heavy intermediate results in `#temp`.
- Write conflicts are detected **per table**, also on different rows (error 24556): two parallel writers on one table can fail by timing.
- A session from a dropped client can stay open with its locks; catalog queries then hang. Find it in `sys.dm_exec_sessions` (`open_transaction_count > 0`). Try a migration inside `BEGIN TRANSACTION ... ROLLBACK` only on a stable connection.

## Running a query

`python tools/fabric/wh_sql.py <server> WH_DWH "<query>"` or `@<file>.sql` (DEV, as the AI identity; Fabric pack).

## Debugging

"Invalid object name" → schema, exact case, two-part name. Still unclear → search Microsoft Learn (the Microsoft Learn MCP server, if connected) for the exact error text before guessing.
