# nogamy-db-objects — Microsoft Fabric

Read when `_context/platform.md` §2 names Fabric. Answers the "Platform specifics" topics of `SKILL.md` for the Fabric Warehouse. A project override goes in `_context/platform.md` §10 → `nogamy-db-objects`.

Needs the Fabric pack (`tools/fabric/`, `tools/migrate/`, `PROJECT.md` → `Packs: fabric`). Missing → run `nogamy-add-pack` first.

## Where

```
fabric/data/WH_DWH.Warehouse/<SCHEMA>/<Tables|Views|StoredProcedures|Functions>/<OBJECT>.sql
```

- The folder is the warehouse's SQL project, in the format Fabric Git integration writes (`fabric/README.md`).
- Object files hold `CREATE` only. `CREATE OR ALTER` is for migrations, never in object files.
- The skill rule "any change under `db/`" reads here as "any change under `fabric/data/WH_DWH.Warehouse/`". The development map is `fabric/data/DEV_MAP.md`, from `python tools/dev_map.py` (the Fabric version of the tool reads the `.Warehouse` folder; a `dev_map.py` that reads only `db/` does not see these files: say so, do not edit the map by hand).
- Run order and dependencies of loads: one line per pipeline in `fabric/data/pipelines/<project>/README.md` (dims before facts).

## Why `TRY_` matters more here

The whole warehouse moves as one item in a deployment, and the drift check compares DEV to the repo: a permanent object without a file is either deployed by accident or reported as drift on every run.

## Platform specifics

| Topic | Fabric Warehouse |
|---|---|
| Folder root and folder names | above; procedures in `StoredProcedures/` |
| Types | `varchar` (UTF-8), `int`, `bigint`, `decimal(p,s)`, `date`, `datetime2(0..6)`, `bit`. No `nvarchar`, `datetime`, `money`, `text` |
| Constraints and indexes | `PRIMARY KEY NONCLUSTERED ... NOT ENFORCED` only. No user indexes. Uniqueness is proven by checks. PK policy options: none (base default) / PK `NOT ENFORCED` on the logical key / per table |
| `ALTER TABLE` | only adding nullable columns and `DROP COLUMN` (`ALTER COLUMN` is preview). Renames via `sp_rename`, in a migration. Anything else on a table: new table + copy, in a migration |
| Transactions, error handling, `MERGE` | supported: `MERGE`, `TRUNCATE`, transactions, `TRY/CATCH`, `THROW`, `IDENTITY`. Frame: `fabric-load-procedure-templates.md` |
| Temp tables | `#name`, session scoped; no `##global`. Distributed form (Microsoft's recommendation): `CREATE TABLE #CUSTOMER_CHANGES (KEY_CUSTOMER INT, CHANGE_TS DATETIME2(6)) WITH (DISTRIBUTION = ROUND_ROBIN);` |
| How migrations are applied to DEV | `python tools/migrate/run_migrations.py <server> [--warehouse WH_DWH] [--dry-run] [--as-agent]`. `--rerun <n>`: DEV only, a migration of a branch not merged yet, after it was rewritten (e.g. `TRY_` names replaced by final names). `--as-agent` refuses any pending file with `DROP` |
| Truncate inside a transaction; backup of one table | not answered by the core yet → verify (`nogamy-platform-watch`) and record in `_context/platform.md` §10 |
| Known traps | write conflicts are detected per table (`nogamy-write-sql` → `references/fabric.md`) |

## Try-outs and DEV cleanup

- The drift check is `python tools/fabric/drift_check.py` (command in `PROJECT.md` → Agent tools). It lists objects in DEV without a file; the developer drops them, the AI reports.
- An approved try-out: rewrite the branch migration with the final names, then `run_migrations.py ... --rerun <n>` in DEV.
