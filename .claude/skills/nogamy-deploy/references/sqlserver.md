# nogamy-deploy — SQL Server / Azure SQL Database

Read when `_context/platform.md` §2 names SQL Server or Azure SQL Database. The project's choice goes in `_context/platform.md` §5 and §6; this file lists the options and their facts.

**Azure SQL DB** marks where Azure SQL Database differs from SQL Server on-premises.

## Two ways to move database code. Pick one per project

| | A. Migrations (core default) | B. State-based: SQL project → DACPAC |
|---|---|---|
| What is in Git | `db/` object files + `scripts/migrations/NNNN_*.sql` | an SDK-style SQL project (`.sqlproj`, `Microsoft.Build.Sql`) in `db/` + `scripts/migrations/` only for data moves, renames, backfills |
| How a target gets there | `python tools/run_migrations.py --profile <env>`: pending files in number order, logged in `MNG.MNG_MIGRATION_LOG` | `dotnet build` → `.dacpac`; `SqlPackage /Action:Publish` compares it with the target and changes the difference |
| Review before running | the migration files themselves | `SqlPackage /Action:Script` (the T-SQL it would run) or `/Action:DeployReport` (XML list of changes) against the target, attached to the deployment note |
| Strong at | exact, repeatable steps; data moves | no hand-written `ALTER`; drift shows up as a diff |
| Watch | every statement guarded (`nogamy-db-objects`) | keep `BlockOnPossibleDataLoss=True` (default) and `DropObjectsNotInSource=False` (default): no silent drop. One pre- and one post-deployment script per project; they run on every publish, so they are idempotent |

- Never both for the same object: two mechanisms, two truths.
- B on an existing database: `SqlPackage /Action:Extract /p:ExtractTarget=SqlProject` creates the project from DEV once; then the repo leads.

## CI/CD options (the project chooses; record in `PROJECT.md` → DevOps)

| Runner | Azure SQL DB | SQL Server on-premises |
|---|---|---|
| A. migrations | a job runs `tools/run_migrations.py --profile <env>` | the same, on an agent that can reach the server |
| B. GitHub Actions | the `azure/sql-action` action (Microsoft's example pins version 2.3), `action: publish`, `path: <file>.dacpac` | a self-hosted runner with SqlPackage. verify: `azure/sql-action` against an on-prem server |
| B. Azure DevOps | task `SqlAzureDacpacDeployment@1` (`DacpacFile`, service connection) | SqlPackage on a self-hosted agent (script step) |
| by hand | the DBA runs the same command or the run sheet | the same |

- **Azure SQL DB**: the runner's IP must be allowed by the server firewall (a rule added and removed by the pipeline), or the run fails to connect (error 40615).
- Secrets (connection strings with passwords, service principal values) live in the runner's secret store, never in the repo.

## Platform specifics — answers (defaults; the project fills its own row in §5)

| Topic | DEV → TEST | TEST → PROD |
|---|---|---|
| Mechanism | A or B, above | the same as DEV → TEST |
| Trigger, and who | per project; never the AI | a person (`PROJECT.md` → People and roles); never the AI |
| How migrations are applied | A: `run_migrations.py`, number order, first. B: `SqlPackage /Action:Publish`, then `run_migrations.py` for the data moves | same |
| How ETL items move | not part of the database: the ETL tool's own path (SQL Agent jobs, SSIS, Data Factory…; `nogamy-build-pipeline`) | same |
| How the BI model and reports move | the BI tool's own path (`nogamy-semantic-model`) | same |
| Per-environment values | SQLCMD variables (`SqlPackage /v:<name>=<value>`) or a config table seeded per environment; never an environment name inside an object | same |
| What the mechanism does not move | data; anything outside the database (logins, SQL Agent jobs in `msdb`) unless scripted. B: contained users move, their passwords do not (SqlPackage sets a random one); seed only through the post-deployment script | same |
| Backup before a risky change; rollback | on-prem: a full backup or a database snapshot by the DBA; a table copy (`SELECT ... INTO`). **Azure SQL DB**: automatic backups; point-in-time restore creates a new database (it cannot overwrite); a table copy in the same database (`nogamy-db-objects` → `references/sqlserver.md`) | same |
| Release window, outside approvals | per project (`_context/platform.md` §5) | per project |

## Test document on SQL Server

- Section 1, A: the log rows in `MNG.MNG_MIGRATION_LOG` have `IS_EXECUTED = 1` and no `ERROR_MSG`. B: the publish output, and a `DeployReport` after it that lists no changes.
- Run order after the deploy: the load procedures (`EXEC SILVER.SP_<TABLE>`), then the checks (`qa/data/`).

## Known traps

- **Azure SQL DB**: no SQL Agent; schedules run in elastic jobs or the ETL tool. No `USE`, no cross-database names: one target database per connection.
- B: renames go through a migration (`scripts/README.md`), never as an edit of the object file alone. verify: whether SqlPackage publishes a rename without the project's refactor log as drop + add.
- B: `GenerateSmartDefaults` (default `False`), when on, invents a default for a new `NOT NULL` column on a table that has rows. Leave it off; write the default in the object file.

## Sources

- https://learn.microsoft.com/en-us/sql/tools/sqlpackage/sqlpackage
- https://learn.microsoft.com/en-us/sql/tools/sqlpackage/sqlpackage-publish
- https://learn.microsoft.com/en-us/sql/tools/sqlpackage/sqlpackage-extract
- https://learn.microsoft.com/en-us/sql/tools/sqlpackage/sqlpackage-deploy-drift-report
- https://learn.microsoft.com/en-us/sql/tools/sql-database-projects/sql-database-projects
- https://learn.microsoft.com/en-us/sql/tools/sql-database-projects/concepts/pre-post-deployment-scripts
- https://learn.microsoft.com/en-us/azure/azure-sql/database/connect-github-actions-sql-db
- https://learn.microsoft.com/en-us/azure/devops/pipelines/targets/azure-sqldb
- https://learn.microsoft.com/en-us/azure/azure-sql/database/recovery-using-backups
- https://learn.microsoft.com/en-us/azure/azure-sql/database/transact-sql-tsql-differences-sql-server
- https://learn.microsoft.com/en-us/azure/azure-sql/database/elastic-jobs-overview
- https://learn.microsoft.com/en-us/azure/azure-sql/database/troubleshoot-common-errors-issues
- https://learn.microsoft.com/en-us/sql/relational-databases/databases/database-snapshots-sql-server
