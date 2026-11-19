# nogamy-build-table — Microsoft Fabric

Read when `_context/platform.md` §2 names Fabric. Changes only where the files go and how DEV is run; the contract in `SKILL.md` is the same.

Needs the Fabric pack (`tools/fabric/`, `tools/migrate/`, `PROJECT.md` → `Packs: fabric`). Missing → run `nogamy-add-pack` first.

## Outputs on Fabric

| # | File |
|---|---|
| 1 | `fabric/data/WH_DWH.Warehouse/GOLD/Tables/<TABLE>.sql` |
| 2 | `fabric/data/WH_DWH.Warehouse/SILVER/Views/V_<TABLE>.sql` |
| 3 | `fabric/data/WH_DWH.Warehouse/SILVER/Tables/SILVER_<TABLE>.sql` |
| 4 | `fabric/data/WH_DWH.Warehouse/SILVER/StoredProcedures/SP_<TABLE>.sql` |
| 5–8 | as in `SKILL.md` (`scripts/migrations/`, `scripts/seed/`, `qa/data/`, the STT) |

`<TABLE>` carries the project prefix only if `nogamy-naming` (or the project's naming rules) says so.

## Running in DEV

At L3 (the Fabric default) the AI runs the DEV loop itself (`nogamy-dev-workflow` → `references/fabric.md`):

1. Apply the migration: `python tools/migrate/run_migrations.py <server> --as-agent`.
2. Run the load twice, the checks after each: `python tools/fabric/wh_sql.py <server> WH_DWH "EXEC SILVER.SP_<TABLE>"`, then `... @qa/data/<GOLD TABLE>.sql`.
3. Drift check: `python tools/fabric/drift_check.py <workspace> fabric/data <server>`.
4. The table's pipeline line and run order: `nogamy-build-pipeline`.

The semantic model descriptions go to the TMDL of the model (`nogamy-semantic-model`).
