# nogamy-dev-workflow — Azure Data Factory

Read when `_context/platform.md` §2 names Azure Data Factory (or Synapse pipelines, where noted).

No pack and no core tool for ADF. The AI uses the Azure CLI `datafactory` extension (installs itself on first use; CLI 2.15.0+), the REST API or Az PowerShell, as its own identity.

## Access and the DEV-only guard

- The AI identity (a service principal) has **Data Factory Contributor on the DEV factory only**. No role on TEST or PROD factories: that role scope is the guard, since the CLI has no allow list.
- verify: that the role scoped to the factory resource (not the resource group) is enough for `create`, `create-run` and the run queries.
- That role can also delete items. The AI never runs a `delete` command, and never starts or stops a trigger (a schedule belongs to a person).
- Run history is kept 45 days.

## The DEV factory is in Git mode: what that means for the AI

- Studio edits a branch. The live DEV factory changes only by Publish (collaboration branch) or by an API call.
- An AI publish by CLI goes **straight to live DEV and is not entered into Git**. The repo file stays the truth; the next publish from the collaboration branch overwrites it.
- After the merge, the DEV live factory is brought back to the collaboration branch: Publish, or "Overwrite live mode" (a person). A try-out item the AI created stays in live DEV until the developer deletes it.
- At L1–L2, or when the project prefers it: the developer runs Debug in Studio on the feature branch, without publishing, and pastes back the run output. verify: Debug runs the branch version unpublished.

## 3. Run in DEV

| What | Command (Az CLI) |
|---|---|
| publish a pipeline to DEV | `az datafactory pipeline create -g <DEV rg> --factory-name <DEV factory> -n <PL_name> --pipeline @etl/adf/pipeline/<PL_name>.json` |
| run it | `az datafactory pipeline create-run -g <DEV rg> --factory-name <DEV factory> -n <PL_name> --parameters '{"P_Name":"value"}'` → `runId` |
| its status | `az datafactory pipeline-run show -g <DEV rg> --factory-name <DEV factory> --run-id <runId>`; poll every 15–30 s while `Queued` or `InProgress` |
| every activity | `az datafactory activity-run query-by-pipeline-run -g <DEV rg> --factory-name <DEV factory> --run-id <runId> --last-updated-after <ISO time> --last-updated-before <ISO time>`: `status`, `error.message`, `output` per activity |
| stop a run | `az datafactory pipeline-run cancel … --run-id <runId> --is-recursive true` (also its children) |
| database change | `python tools/run_migrations.py` (DEV profile, `--as-agent`), never the object file directly |

- verify: whether `--pipeline` takes the Git file as it is (`name` + `properties`) or only its `properties` object. Test once in DEV and record it in `_context/platform.md` §10.
- verify: `az datafactory dataset create` and `linked-service create` for those items; a linked service with a secret is created by a person.
- A child pipeline has its own run. verify: its `runId` is in the parent's `ExecutePipeline` activity output; read the child's activities with it.
- Final status values: `Succeeded`, `Failed`, `Cancelled` (also `Queued`, `InProgress`, `Canceling`).

Same calls without the CLI:
- REST: `POST https://management.azure.com/subscriptions/<sub>/resourceGroups/<rg>/providers/Microsoft.DataFactory/factories/<factory>/pipelines/<name>/createRun?api-version=2018-06-01`, body = the parameters; then `POST …/pipelineruns/<runId>/queryActivityruns` with `lastUpdatedAfter`, `lastUpdatedBefore`.
- PowerShell: `Invoke-AzDataFactoryV2Pipeline` (returns the run ID), `Get-AzDataFactoryV2PipelineRun -PipelineRunId`, `Get-AzDataFactoryV2ActivityRun -PipelineRunId -RunStartedAfter -RunStartedBefore`.

## 5. Compare repo with DEV

- No core drift tool for ADF. Compare `az datafactory pipeline show … -n <name>` with the repo file, item by item, ignoring the fields ADF adds (verify which: e.g. `etag`, `lastPublishTime`).
- `az datafactory pipeline list -g <DEV rg> --factory-name <DEV factory>`: items in DEV without a file are listed in the hand-over.
- A project tool for this goes in `tools/project/`.

## Platform specifics — answers

| Topic | Azure Data Factory |
|---|---|
| Access level | per project (`_context/platform.md` §7). L3 is possible with the CLI and the DEV-only role |
| Folder layout | `etl/adf/` (ADF root folder: `pipeline/`, `dataset/`, `linkedService/`, `trigger/`…; `nogamy-build-pipeline`); database objects under `db/` |
| Run a query / a `.sql` file in DEV | the target database's command line (`nogamy-write-sql`, `_context/platform.md` §10). ADF has none |
| Apply migrations in DEV | `python tools/run_migrations.py` (`--as-agent`, DEV profile) |
| Publish an ETL item to DEV | `az datafactory pipeline create … --pipeline @<file>` (not in Git; see above) |
| Run an ETL item and read its steps | `create-run`, `pipeline-run show`, `activity-run query-by-pipeline-run`; Studio: Monitor → the run → each activity's input, output, error |
| Compare repo with DEV | `pipeline show` / `pipeline list` against `etl/adf/` (above) |
| By hand in the UI | Git configuration; Publish or "Overwrite live mode" after the merge; self-hosted IR install; Key Vault access for the factory; linked services with secrets |

Synapse: the same loop with `az synapse pipeline create` and `az synapse pipeline create-run` (verify the exact parameters).

## Sources

- https://learn.microsoft.com/en-us/cli/azure/datafactory/pipeline
- https://learn.microsoft.com/en-us/cli/azure/datafactory/pipeline-run
- https://learn.microsoft.com/en-us/cli/azure/datafactory/activity-run
- https://learn.microsoft.com/en-us/rest/api/datafactory/pipelines/create-run
- https://learn.microsoft.com/en-us/rest/api/datafactory/activity-runs/query-by-pipeline-run
- https://learn.microsoft.com/en-us/azure/data-factory/monitor-programmatically
- https://learn.microsoft.com/en-us/powershell/module/az.datafactory/invoke-azdatafactoryv2pipeline
- https://learn.microsoft.com/en-us/azure/data-factory/concepts-roles-permissions
- https://learn.microsoft.com/en-us/azure/role-based-access-control/built-in-roles/analytics
- https://learn.microsoft.com/en-us/azure/data-factory/source-control
