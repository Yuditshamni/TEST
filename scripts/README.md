# scripts/ — what reaches every environment by script

Every change to the database reaches each environment through a migration script. Who runs them in each environment, and how (by hand, a runner, CI/CD): `_context/platform.md` §5 and §6, skill `nogamy-deploy`.

| Folder | What | When it runs | Rule |
|---|---|---|---|
| `migrations/` | **every** database change: create, change, drop, data move | in every environment, in number order | numbered, logged, safe to run twice |
| `seed/` | config rows (load config, quality checks, watermarks) | after the migrations that create the tables | idempotent |
| `grants/` | grants and roles per schema | after migrations that add schemas or objects | idempotent |

A project whose platform deploys database code by comparing states (`_context/platform.md` §6) uses `migrations/` only for what a compare cannot do: data moves, renames, backfills.

## Migrations

**Two files for every database change, in the same PR:**

| File | Role |
|---|---|
| `db/<SCHEMA>/<Type>/<OBJECT>.sql` | how the object looks now. Edited in place; the place to read an object |
| `scripts/migrations/NNNN_<what>.sql` | how an environment gets there from the previous migration |

**File rules**

- Name: `NNNN_<what>.sql`. **The number is the run order.** Several migrations in one PR get consecutive numbers in the order they must run.
- Take the next free number on the main branch. Two open branches took the same number → the one merged second renumbers **before** its merge. After merge a number never changes.
- Header: `-- migration: NNNN`, `-- PR: <branch or PR>`, then one plain sentence: what it does and why. That sentence is its description in the log.
- **Safe to run twice**: a failed run is re-run from the top. Every statement is guarded, in the project's dialect (`_context/platform.md` §6):

| Change | Guard (examples; use the project's dialect) |
|---|---|
| new schema, table | create only if it does not exist: `CREATE … IF NOT EXISTS`, or `IF OBJECT_ID('S.T') IS NULL CREATE …` |
| new or changed view, procedure, function | `CREATE OR REPLACE …` / `CREATE OR ALTER …` |
| new column | add only if the column is not in the catalog |
| drop | `DROP … IF EXISTS` |
| rename, type change, data move | new object + copy + drop of the old, in one file, each step guarded |

- One topic per file. The object file and the migration must say the same thing: the review checks it.

**The log, inside each database**

`MNG.MNG_MIGRATION_LOG`, one row per migration file: `RUN_ORDER`, `FILE_NAME`, `DESCRIPTION`, `IS_EXECUTED`, `EXECUTED_AT`, `EXECUTED_BY`, `ERROR_MSG`.

- Git says what changed. The log says what each environment actually has.
- Pending files run by `RUN_ORDER`, lowest first. A failure writes `ERROR_MSG` and stops: nothing after it runs.
- What is missing in an environment: `SELECT RUN_ORDER, FILE_NAME FROM MNG.MNG_MIGRATION_LOG WHERE IS_EXECUTED = 0 ORDER BY RUN_ORDER;`
- Migration `0001` creates the `MNG` schema and the log table itself.
- Run by a tool: `python tools/run_migrations.py --profile <env>` (any of sqlserver, fabric, snowflake, postgres, databricks) registers every file, runs the pending ones, writes the rows. `--check` checks names, numbers and headers offline.
- Run by hand (access level L0, or a platform without a dialect in the runner): `python tools/run_migrations.py --platform <closest> --run-sheet --from <first pending>` writes each file with its log statements, in order, for any SQL tool.
- Migration `0001`: `python tools/run_migrations.py --platform <platform> --print-log-ddl` gives the schema and the log table, guarded.

**What is not a migration**

- A migration describes a change **from what is on the main branch**. It runs in every environment and stays in every log.
- Leftovers of a try-out on a branch that was never merged exist only in DEV. They are **not** a migration: in TEST and PROD they never existed. The developer drops them by hand in DEV before the PR; the PR description lists them under "DEV cleanup before merge".
- A branch's own migrations may be rewritten freely until merge. After merge they are frozen.

Owner: data engineer.
