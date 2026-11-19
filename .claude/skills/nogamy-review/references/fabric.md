# nogamy-review — Microsoft Fabric

Read when `_context/platform.md` §2 names Fabric. These checks are added to the checklist in `SKILL.md`.

## Structure

- [ ] one object per file under `fabric/data/WH_DWH.Warehouse/<SCHEMA>/<Tables|Views|StoredProcedures>/`, `CREATE` only (the change itself is in the migration)
- [ ] the migration in `scripts/migrations/NNNN_<what>.sql` ran in DEV through `tools/migrate/run_migrations.py` (row in `MNG.MNG_MIGRATION_LOG` with `IS_EXECUTED = 1`)

## Method

- [ ] references are `schema.object`, never three-part (`WH_DWH.GOLD.X`)
- [ ] `python tools/dev_map.py --check` passes: `fabric/data/DEV_MAP.md` matches the `.sql` files
- [ ] no permanent work tables in `WH_DWH`: `#temp`, or `TRY_` for a try-out
- [ ] T-SQL style: UPPERCASE keywords, one column per line

## Platform (Fabric Warehouse, Data Factory)

- [ ] only types the Fabric Warehouse supports: `varchar`, `datetime2(n)` with `n ≤ 6`; no `nvarchar`, no `datetime`
- [ ] pipelines (`fabric/data/pipelines/<project>/X.DataPipeline/pipeline-content.json`): no hard-coded workspace, item or connection IDs, no endpoints; environment values come from the Variable library
- [ ] stored procedure activities: `retry: 0`
- [ ] every new pipeline has a line in `fabric/data/pipelines/<project>/README.md`: what it does, its trigger, its dependencies
- [ ] drift check clean: `python tools/fabric/drift_check.py <DEV workspace> fabric/data <DEV SQL endpoint>` (exit code 0). It compares definitions only: the pipeline was also run in DEV (`tools/fabric/run_pipeline.py`)
