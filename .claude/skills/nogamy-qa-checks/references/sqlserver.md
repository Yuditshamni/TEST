# nogamy-qa-checks — SQL Server / Azure SQL Database

Read when `_context/platform.md` §2 names SQL Server or Azure SQL Database. The checks in `SKILL.md` are the same; this file says how they run in T-SQL.

**Azure SQL DB** marks where Azure SQL Database differs from SQL Server on-premises.

## Running checks

- Per-table checks: `sqlcmd -S <server> -d <database> -E -b -i qa/data/<GOLD TABLE>.sql` (DEV, as the AI identity, at the level in `_context/platform.md` §7; **Azure SQL DB**: `-G` instead of `-E`). Then the load again, and the checks again.
- At L0 the same file goes into the run sheet; the person pastes the result table.
- The SQL is T-SQL (`nogamy-write-sql` → `references/sqlserver.md`): `TOP (n)`, `LEN`, `COUNT_BIG`. A person's look at 100 rows: `SELECT TOP (100) ...`, run by the person, never by the AI on sensitive columns.

## Checks that matter more here

| Check | Why on SQL Server |
|---|---|
| duplicates on the key, also by exact spelling: `GROUP BY KEY_CODE COLLATE Latin1_General_100_BIN2` | the default collation is case insensitive: `'a1'` and `'A1'` count as one key in a plain `GROUP BY`, but are two in a case-sensitive source or BI tool |
| trailing spaces in keys: `DATALENGTH(KEY_CODE) <> DATALENGTH(RTRIM(KEY_CODE))` | `=` ignores trailing spaces, so a join hides them |
| Hebrew text intact: no `varchar` business-text column without a Hebrew or `_UTF8` collation (`INFORMATION_SCHEMA.COLUMNS.COLLATION_NAME`) | a code page without Hebrew cannot store it |
| enforced constraints, if the project has them | a duplicate fails the load (error 2627 / 2601) before the check runs: the check still runs on staging |

## The quality framework on SQL Server

No pack: the base names hold (`MNG.MNG_DQA_QUERY`, `MNG.MNG_DQA_RESULT`, `MNG.SP_DQA`; `nogamy-naming`), as files in `db/MNG/`.

- A failed check stops the caller: `MNG.SP_DQA` ends with `THROW 50001, N'<message>', 1;` (a user error number is 50000 or higher; `THROW` raises severity 16).
- Severity 16 makes `sqlcmd -b` exit with code 1. verify: that the project's runner (SQL Agent T-SQL step, ETL activity) marks the step failed on it, once in DEV.
- Write the result row **before** the `THROW`, outside the load's transaction, or the rollback removes it (`MNG_DQA_RESULT` is never deleted).
- Gates per `nogamy-build-pipeline`: after each bronze load, after the dimensions, after the facts.

## Golden questions

Asked of the BI model or the AI assistant the project uses (`_context/platform.md` §2, `nogamy-semantic-model`). A wrong answer is fixed in the model.

## Sources

- https://learn.microsoft.com/en-us/sql/t-sql/language-elements/throw-transact-sql
- https://learn.microsoft.com/en-us/sql/tools/sqlcmd/sqlcmd-utility
- https://learn.microsoft.com/en-us/sql/relational-databases/collations/collation-and-unicode-support
- https://learn.microsoft.com/en-us/sql/t-sql/language-elements/string-comparison-assignment
- https://learn.microsoft.com/en-us/sql/relational-databases/errors-events/database-engine-events-and-errors-2000-to-2999
- https://learn.microsoft.com/en-us/sql/relational-databases/system-tables/dbo-sysjobhistory-transact-sql
