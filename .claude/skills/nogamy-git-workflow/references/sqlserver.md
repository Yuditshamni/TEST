# nogamy-git-workflow — SQL Server / Azure SQL Database

Read when `_context/platform.md` §2 names SQL Server or Azure SQL Database. The rules in `SKILL.md` are the same; this file says how definitions travel between the database and the repo. Project facts (provider, approvers) stay in `_context/platform.md` §4.

## The database does not sync with Git

- Neither SQL Server nor Azure SQL Database has a Git integration of its own. The repo is written first, DEV is filled from it, and the two are compared before every PR (`nogamy-dev-workflow` → `references/sqlserver.md` step 5).
- An object changed in DEV by hand (SSMS, VS Code) is drift until its file and its migration are in the branch.

## Plain files or a SQL project

| | Plain files (core default) | SDK-style SQL project (`Microsoft.Build.Sql`) |
|---|---|---|
| In `db/` | `<SCHEMA>/<Type>/<OBJECT>.sql` | the same object files + `<name>.sqlproj`; all `.sql` files in the folder are included by default |
| Proof that the files are coherent | migrations run in DEV | `dotnet build` (a broken reference fails the build) |
| Deploy | migrations (`nogamy-deploy`) | `.dacpac` + SqlPackage; migrations for data moves only |
| Tools | any editor | VS Code (SQL Database Projects, GA), `dotnet` CLI; Visual Studio for the original project format |

The choice is the project's, recorded in `_context/platform.md` §6. The older (non-SDK) `.sqlproj` format still works; Microsoft points new work to the SDK style.

## Platform specifics — answers

| Topic | SQL Server / Azure SQL Database |
|---|---|
| Provider, repo, main branch | per project (`_context/platform.md` §4) |
| How the repo is reached | per project |
| Who approves a PR; required checks | per project; with a SQL project, `dotnet build` is a natural required check |
| Who merges core-update PRs | `PROJECT.md` → People and roles |
| May the AI push or open a PR? | no (default) |
| Platform ↔ Git sync | none in the database; the repo leads |
| Tool → file (an object that exists only in a database) | views, procedures, functions: the definition from `sys.sql_modules.definition` (or `OBJECT_DEFINITION`). Whole database once: `SqlPackage /Action:Extract /p:ExtractTarget=SchemaObjectType` (one file per object, folders per schema and type) or `ExtractTarget=SqlProject`, to a scratch folder; then copy into `db/` with the core's folder names |
| File → tool | a numbered migration (`tools/run_migrations.py`), or the SQL project's publish (`nogamy-deploy`) |
| Text formats in the repo | `.sql`; `.sqlproj` (XML); `.scmp` schema-compare files (XML) if the team keeps them |
| Not in Git, and where it is recorded | `.dacpac` (a build output, a zip archive) and the build folder `bin/`: `.gitignore`. `_private/db-profiles.json` (profiles; secrets in the OS credential store). Connection strings with passwords, SQLCMD variable values that are secrets: the runner's secret store |

## Known traps

- `sp_rename` of a view or procedure does not change the name inside `sys.sql_modules.definition`: a definition copied from DEV after a rename can carry the old name. Check the `CREATE` line before committing.
- `ExtractTarget=SchemaObjectType` folder names may differ from `Tables/Views/Procedures/Functions`. verify: the exact folder names SqlPackage writes, before mapping them to `db/`.

## Sources

- https://learn.microsoft.com/en-us/sql/tools/sql-database-projects/sql-database-projects
- https://learn.microsoft.com/en-us/sql/tools/sql-database-projects/concepts/schema-comparison
- https://learn.microsoft.com/en-us/sql/tools/sql-database-projects/concepts/pre-post-deployment-scripts
- https://learn.microsoft.com/en-us/sql/tools/sqlpackage/sqlpackage-extract
- https://learn.microsoft.com/en-us/sql/relational-databases/system-stored-procedures/sp-rename-transact-sql
