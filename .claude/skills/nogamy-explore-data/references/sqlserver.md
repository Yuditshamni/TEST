# nogamy-explore-data — SQL Server / Azure SQL Database

Read when `_context/platform.md` §2 names SQL Server or Azure SQL Database. The rules in `SKILL.md` are the same; this file says how to run the profile in T-SQL.

- Run in DEV only, as the AI identity, at the level in `_context/platform.md` §7: `sqlcmd -S <server> -d <database> -E -b -i <profile>.sql` (**Azure SQL DB**: `-G` instead of `-E`). The command is also in `PROJECT.md` → Agent tools.
- T-SQL: `LEN(col)` instead of `LENGTH(col)`. `LEN` ignores trailing spaces: add `MAX(DATALENGTH(col))` to see them (bytes, not characters).
- Never `SELECT TOP (n) *` on a table with sensitive columns.
- Structure: `INFORMATION_SCHEMA.COLUMNS` (`DATA_TYPE`, `CHARACTER_MAXIMUM_LENGTH`, `IS_NULLABLE`, `COLLATION_NAME`) or `sys.columns`.
- Row count of a big table without a scan: `SELECT SUM(row_count) FROM sys.dm_db_partition_stats WHERE object_id = OBJECT_ID(N'BRONZE.BRONZE_CRM_CUSTOMERS') AND index_id IN (0, 1);` (approximate; the profile itself counts with `COUNT_BIG(*)`).
- `COUNT` returns `int`; past about 2.1 billion rows use `COUNT_BIG`.

## Case and spaces hide in the default collation

- The usual collation is case insensitive (`_CI_`): `COUNT(DISTINCT CODE)` counts `'A'` and `'a'` as one value. Flag mixed case with a binary count:
  `SELECT COUNT(DISTINCT CODE) AS CI_VALUES, COUNT(DISTINCT CODE COLLATE Latin1_General_100_BIN2) AS EXACT_VALUES FROM ...;` — a difference = mixed spellings.
- `=` ignores trailing spaces (ANSI padding): `'A' = 'A '` is true, so a key join hides them. Count `SUM(CASE WHEN DATALENGTH(CODE) <> DATALENGTH(RTRIM(CODE)) THEN 1 ELSE 0 END)`.
- A `varchar` text column whose `COLLATION_NAME` is neither Hebrew nor `_UTF8` cannot hold Hebrew: flag it, with the column's collation.

## Masked columns

Dynamic data masking (SQL Server 2016+, Azure SQL DB) returns masked values to users without `UNMASK`. Useful for the AI's identity in DEV, but Microsoft warns that ad-hoc queries can infer masked values: it limits exposure, it does not replace "never read sensitive rows".

## Sources

- https://learn.microsoft.com/en-us/sql/t-sql/functions/len-transact-sql
- https://learn.microsoft.com/en-us/sql/relational-databases/system-dynamic-management-views/sys-dm-db-partition-stats-transact-sql
- https://learn.microsoft.com/en-us/sql/relational-databases/collations/collation-and-unicode-support
- https://learn.microsoft.com/en-us/sql/t-sql/language-elements/like-transact-sql
- https://learn.microsoft.com/en-us/sql/t-sql/language-elements/string-comparison-assignment
- https://learn.microsoft.com/en-us/sql/t-sql/functions/count-transact-sql
- https://learn.microsoft.com/en-us/sql/relational-databases/security/dynamic-data-masking
- https://learn.microsoft.com/en-us/sql/tools/sqlcmd/sqlcmd-utility
