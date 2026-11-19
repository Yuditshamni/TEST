# nogamy-platform-watch — SQL Server / Azure SQL Database

Read when `_context/platform.md` §2 names SQL Server or Azure SQL Database.

## Source

Microsoft Learn only (the Fabric pack's `microsoft-learn` MCP server works here too, when the project has it; else the pages by web access, or "not verified").
Start of each daily check: "What's new in SQL Server" for the project's version, and for Azure SQL Database its "What's new" page; then each watch-list item.

## Watch list topics

| Topic | Why we watch it |
|---|---|
| T-SQL surface per version: `CREATE OR ALTER`, `DROP ... IF EXISTS`, `STRING_AGG`, `IS [NOT] DISTINCT FROM`, `GREATEST` / `LEAST`, UTF-8 collations | which guards and patterns a migration may use (`nogamy-write-sql`, `nogamy-db-objects`) |
| `MERGE` known issues and fixes | the merge load pattern (`nogamy-bronze-load`, `nogamy-db-objects`) |
| Azure SQL Database: features that differ from SQL Server (cross-database queries, SQL Agent, Windows sign-in) | what the runner and the jobs can rely on (`nogamy-dev-workflow`, `nogamy-deploy`) |
| `mssql-python` driver: sign-in options (`Authentication=` values for Microsoft Entra ID), Linux requirements | `tools/run_migrations.py` connects with it (`nogamy-dev-workflow`) |
| SqlPackage / SQL projects (SDK-style): publish options, rename handling, `azure/sql-action` | promotion when the project deploys by state compare (`nogamy-deploy`, `nogamy-git-workflow`) |
| Lifecycle: end of support of the project's version | a version out of support changes what we recommend to the client |
