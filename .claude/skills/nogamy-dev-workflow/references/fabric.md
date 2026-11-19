# nogamy-dev-workflow — Microsoft Fabric

Read when `_context/platform.md` §2 names Microsoft Fabric.

Needs the Fabric pack (`tools/fabric/`, `tools/migrate/`, `PROJECT.md` → `Packs: fabric`). Missing → `nogamy-add-pack` first.

## Fabric default: L3, the agent runs the whole DEV loop

With `tools/fabric`, L3 is the norm. After the plan is approved the agent builds, runs the migrations, creates and publishes the pipelines, runs them, checks, commits and runs the drift check, all in the DEV workspace. It never asks the developer to run a migration, create a pipeline in the portal, publish, run or check. The developer keeps: plan approval, PR review, push and merge, anything with `DROP` or delete, permissions, TEST and PROD.

- The agent works only in the DEV workspace (`PROJECT.md` → Environments), as the AI identity named there.
- The tools refuse any workspace that is not on their allow list. TEST, PROD and BI workspaces are never added to it.

## 1. Plan

What exists in DEV: `python tools/fabric/wh_sql.py <server> WH_DWH "<query on sys.objects>"` (structure only).

## 2. Branch and files

```
git switch -c feature/<short-name>
```

| What | Where |
|---|---|
| Warehouse objects | `fabric/data/WH_DWH.Warehouse/<schema>/<Type>/<object>.sql` (Type: Tables, Views, StoredProcedures, Functions) (`nogamy-db-objects`) + the next migration in `scripts/migrations/` |
| Pipelines | `fabric/data/pipelines/<project>/<NN_layer>/<name>.DataPipeline/pipeline-content.json` (`nogamy-build-pipeline`) |
| Checks | `qa/data/<GOLD TABLE>.sql` |

## 3. Run in DEV

| What | How |
|---|---|
| any warehouse change | the migration, the same way it runs in TEST and PROD: `python tools/migrate/run_migrations.py <DEV endpoint> --as-agent`. Never run the object file directly. A migration with `DROP`: the developer runs it without `--as-agent` |
| pipeline | `python tools/fabric/publish_pipeline.py <DEV workspace> <folder>.DataPipeline`: creates the pipeline in its workspace folder when missing, then publishes the definition |
| run a pipeline | `python tools/fabric/run_pipeline.py <DEV workspace> <pipeline>` (prints the status and `failureReason`) |
| run checks | `python tools/fabric/wh_sql.py <server> WH_DWH @qa/data/<table>.sql` |

Try-outs: `#temp` tables only (session scoped; `##global` temp tables are not supported in the Warehouse).

## 5. Commit and drift check

```
git add <files>
git commit -m "<scope>: <what> — <why>"
python tools/fabric/drift_check.py <DEV workspace> fabric/data <server>
```

- `DIFF` = the repo and DEV disagree. Fix before the PR.
- Objects in DEV without a file are listed: add the file, or report them.

## Platform specifics — answers

| Topic | Fabric |
|---|---|
| Access level | L3 (default with the Fabric pack) |
| Folder layout | `fabric/data/WH_DWH.Warehouse/...` and `fabric/data/pipelines/<project>/<NN_layer>/...` |
| Run a query / a `.sql` file in DEV | `tools/fabric/wh_sql.py <server> WH_DWH "<sql>"` or `@<file>` |
| Apply migrations in DEV | `tools/migrate/run_migrations.py <DEV endpoint> --as-agent` |
| Publish an ETL item to DEV | `tools/fabric/publish_pipeline.py <DEV workspace> <folder>.DataPipeline` |
| Run an ETL item and read its steps | `tools/fabric/run_pipeline.py <DEV workspace> <pipeline>`; portal: Monitor → the run → each activity's output |
| Compare repo with DEV | `tools/fabric/drift_check.py <DEV workspace> fabric/data <server>` |
| By hand in the UI | nothing in the loop by default; connections and workspace roles are the developer's (`nogamy-build-pipeline`) |
