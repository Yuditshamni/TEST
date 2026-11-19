# nogamy-naming — SQL Server / Azure SQL Database

Read when `_context/platform.md` §2 names SQL Server or Azure SQL Database. The rules in `SKILL.md` still hold; this file adds only what T-SQL changes. A project choice goes in `PROJECT.md` → Project rules → Naming.

## Limits

| What | Limit |
|---|---|
| identifier (schema, table, view, procedure, column) | 1–128 characters |
| local temp table `#NAME` | 116 characters |
| first character | `#` = local temp object, `##` = global temp object, `@` = variable or parameter: never at the start of a permanent name |

## Why exact spelling matters even here

- The usual collation is **case insensitive**: `GOLD.Sales_Dim_Customer` and `GOLD.SALES_DIM_CUSTOMER` are the same object, so a wrong spelling still runs.
- It breaks elsewhere: a case-sensitive BI tool, a binary-collation database, a script compared as text. One exact spelling (`UPPER_SNAKE_CASE`) stays the rule.
- References are two-part (`SCHEMA.OBJECT`). Project objects live in the layer schemas, not `dbo`. Never a database name: **Azure SQL DB** refuses names that point to another database.

## Reserved words

- A T-SQL reserved word as a name needs `[ ]` everywhere: avoid it. Columns that clash in practice: `KEY`, `USER`, `PLAN`, `FILE`, `PERCENT`, `RULE`, `OPEN`, `STATISTICS`, `CURRENT_DATE`. The `KEY_<ENTITY>` pattern is safe; a bare `KEY` is not.
- Microsoft also lists ISO / ODBC reserved and future keywords (e.g. `DATE`, `LEVEL`, `VALUE`): allowed today, better avoided as bare column names. Check a new word against the list before the STT is approved.

## `SP_` prefix

- Microsoft advises against the `sp_` prefix (used by system procedures). With a case-insensitive collation `SP_` is the same prefix.
- The base names (`SILVER.SP_<PROJECT>_<TABLE>`, `MNG.SP_DQA`) stay, always called with their schema. Before a new procedure name: no system procedure with that name (`SELECT name FROM sys.all_objects WHERE is_ms_shipped = 1 AND name = N'<name>';` returns nothing). A project that prefers another prefix records it in `PROJECT.md` → Naming.

## Per environment

The database, server and logical server names differ per environment; they live in the connection (profile, runner secret), never in code. Object names are the same in every database.

## Sources

- https://learn.microsoft.com/en-us/sql/relational-databases/databases/database-identifiers
- https://learn.microsoft.com/en-us/sql/t-sql/statements/create-table-transact-sql
- https://learn.microsoft.com/en-us/sql/t-sql/language-elements/reserved-keywords-transact-sql
- https://learn.microsoft.com/en-us/sql/t-sql/statements/create-procedure-transact-sql
- https://learn.microsoft.com/en-us/sql/relational-databases/collations/collation-and-unicode-support
- https://learn.microsoft.com/en-us/azure/azure-sql/database/transact-sql-tsql-differences-sql-server
