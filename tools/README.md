# tools/ — small scripts the team and the AI run

Plain Python or shell, so any AI tool and any person can run them. No tool here is tied to one AI product.

`tools/` is core (read-only in a project). Tools written for one project go in `tools/project/`.

## Shipped with the core (offline, no database)

| Script | Does |
|---|---|
| `bundle_context.py` | packs `AGENTS.md`, `PROJECT.md`, `_context/` and chosen skills (and their `references/<platform>.md` with `--platform`) and specs into one Markdown file, for a chat tool that cannot read the repo. Writes to `_private/` (not in Git) |
| `run_migrations.py` | applies pending `scripts/migrations/NNNN_*.sql` in order and logs them in `MNG.MNG_MIGRATION_LOG`, on any platform: sqlserver / Azure SQL, fabric, snowflake, postgres, databricks. `--check` (offline), `--dry-run`, `--as-agent` (DEV profile only, refuses `DROP`), `--rerun N` (DEV). No connection or another platform: `--run-sheet` writes the steps for a person to run in any SQL tool. `--print-log-ddl` gives the log table for migration `0001`. Profiles: `_private/db-profiles.json` (top of the script) |
| `new_project.py` | a person (project lead) opens a new project in one command: repo from the core template, `main` protected with `nogamy-core-guard` required, cloned. `--dry-run` prints the steps. The AI never runs it |
| `dev_map.py` | reads `db/**/*.sql`, writes `db/DEV_MAP.md` (Mermaid: tables, views, data flow, dependencies between entities); `--check` exits 1 if the map is out of date |

```
python tools/bundle_context.py --skills specs,explore-data --add stt/sales sources/crm
python tools/bundle_context.py --skills write-sql,db-objects --platform fabric
python tools/dev_map.py
python tools/dev_map.py --check
```

## Fabric pack (`nogamy-add-pack`)

| Script | Does |
|---|---|
| `fabric/wh_sql.py` | run a query or a `.sql` file on the DEV warehouse, as the AI identity |
| `fabric/publish_pipeline.py`, `fabric/run_pipeline.py` | push a pipeline from the repo to DEV; run it and print every step |
| `fabric/publish_variable_library.py` | push the Variable library values to DEV |
| `fabric/drift_check.py` | compare the repo with the live DEV items; exit 1 on a difference |
| `migrate/run_migrations.py` | the Fabric command line of `tools/run_migrations.py` (`<sql endpoint> [--as-agent]`): Fabric sign-in and the `tools/fabric` allow list, same engine and log |

Usage and guard rails: `.claude/skills/nogamy-dev-workflow/references/fabric.md`.

## Added per project, by access level (other platforms, in `tools/project/`)

What the project adds depends on `_context/platform.md` §7. Each one is small, does one thing, and prints what it did.

| Level | Tool | Does |
|---|---|---|
| L1 | `run_sql` | run a query or a `.sql` file on DEV and print the result as a table |
| L3 | `publish_item`, `run_item` | push an ETL item from the repo to DEV; run it, wait, and print the status of every step |
| L1+ | `drift_check` | compare the repo files with the live DEV objects; exit 1 on a difference |

The platform may already have a command-line tool that does one of these. Then the entry in this README is the exact command, not a new script.

## Guard rails for any tool that connects

- Identity and server names come from a config file in `_private/` (not in Git). The secret lives in the operating system's credential store, never in a file.
- An **allow list** of servers and databases. Everything else is refused before a request is sent.
- TEST and PROD are never on the AI's allow list.
- A tool that reaches TEST or PROD runs only in a person's hands, as that person.
