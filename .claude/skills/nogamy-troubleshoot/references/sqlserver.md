# nogamy-troubleshoot — SQL Server / Azure SQL Database

Read when `_context/platform.md` §2 names SQL Server or Azure SQL Database.

**Azure SQL DB** marks where Azure SQL Database differs from SQL Server on-premises.

## 1. Get the facts

- Procedure: run it alone, same parameters: `sqlcmd -S <server> -d <database> -E -b -Q "EXEC <schema>.<procedure> ..."` (**Azure SQL DB**: `-G`). Copy the full message: number, severity, procedure, line.
- SQL Agent job (on-prem): `msdb.dbo.sysjobhistory` for the run: `run_status` (0 failed, 1 succeeded, 3 canceled, 4 in progress), `step_id`, `message`, `sql_message_id`.
- An environment differs: `python tools/run_migrations.py --profile <env> --dry-run` lists what is pending; `MNG.MNG_MIGRATION_LOG` rows with `ERROR_MSG`.
- Blocking or a hang: `sys.dm_exec_requests` (`blocking_session_id`, `wait_type`) — read-only.
- Error text: search it in Microsoft Learn before guessing.

## 2. Known causes on SQL Server

| Symptom | Usual cause | Fix |
|---|---|---|
| `Invalid object name` (208) | wrong schema, the wrong database in the connection, a three-part name (**Azure SQL DB** refuses other databases) | `SCHEMA.OBJECT`; check `-d` in the command |
| `Violation of PRIMARY KEY constraint` (2627) / `Cannot insert duplicate key row` (2601) | duplicates in staging, often two spellings the case-insensitive collation sees as one | find them in staging with a `GROUP BY ... HAVING COUNT(*) > 1`; fix the view |
| `String or binary data would be truncated in table ..., column ...` (2628; older: 8152) | a source value longer than the column | the real length from the source catalog (`nogamy-explore-data`); widen in a migration |
| Hebrew text lost or garbled after a load | `varchar` with a code page without Hebrew, or a literal without `N'...'` | `nvarchar` (or a `_UTF8` collation); `N'...'` |
| `Cannot resolve the collation conflict` (468) | a temp table (tempdb collation) compared with a user table | `COLLATE DATABASE_DEFAULT` on the temp table's text columns |
| `Transaction count after EXECUTE indicates a mismatching number of BEGIN and COMMIT` (266) | a `CATCH` without `ROLLBACK`, or a nested procedure that commits | the frame in `nogamy-db-objects` → `references/sqlserver-load-procedure-templates.md` |
| `Cannot truncate table ... because it is being referenced by a FOREIGN KEY constraint` (4712) | full reload of a dimension with an FK from a fact | the project's FK choice (`nogamy-db-objects` → `references/sqlserver.md`) |
| deadlock victim (1205) | two loads writing the same tables at once | run order (`nogamy-build-pipeline`); re-run |
| `'CREATE VIEW' must be the first statement in a query batch` (111) | a migration without `GO` between batches, or `GO` sent by a tool that does not split | `GO` on its own line; run through `tools/run_migrations.py` or `sqlcmd` |
| a `MERGE` fails with error 10713 | no `;` after `MERGE` | end the statement with `;` |
| `Login failed for user` (18456) | wrong authentication type; **Azure SQL DB** has no Windows authentication | the profile's `connection_string` with Microsoft Entra ID |
| **Azure SQL DB** `Cannot connect` (40615) | the client IP is not in the server firewall | a firewall rule, set by an admin (not the AI) |
| **Azure SQL DB** 40613 / 40501 / 40197 | transient: reconfiguration or busy | retry after a pause; the runner re-runs the migration from the top |

## Sources

- https://learn.microsoft.com/en-us/sql/relational-databases/errors-events/database-engine-events-and-errors-0-to-999
- https://learn.microsoft.com/en-us/sql/relational-databases/errors-events/database-engine-events-and-errors-1000-to-1999
- https://learn.microsoft.com/en-us/sql/relational-databases/errors-events/database-engine-events-and-errors-2000-to-2999
- https://learn.microsoft.com/en-us/sql/relational-databases/errors-events/database-engine-events-and-errors-4000-to-4999
- https://learn.microsoft.com/en-us/sql/relational-databases/system-dynamic-management-views/sys-dm-exec-requests-transact-sql
- https://learn.microsoft.com/en-us/sql/t-sql/statements/alter-database-scoped-configuration-transact-sql
- https://learn.microsoft.com/en-us/sql/t-sql/statements/merge-transact-sql
- https://learn.microsoft.com/en-us/sql/t-sql/statements/truncate-table-transact-sql
- https://learn.microsoft.com/en-us/sql/relational-databases/collations/collation-and-unicode-support
- https://learn.microsoft.com/en-us/sql/t-sql/data-types/nchar-and-nvarchar-transact-sql
- https://learn.microsoft.com/en-us/sql/relational-databases/system-tables/dbo-sysjobhistory-transact-sql
- https://learn.microsoft.com/en-us/sql/t-sql/language-elements/sql-server-utilities-statements-go
- https://learn.microsoft.com/en-us/azure/azure-sql/database/troubleshoot-common-errors-issues
- https://learn.microsoft.com/en-us/azure/azure-sql/database/transact-sql-tsql-differences-sql-server
