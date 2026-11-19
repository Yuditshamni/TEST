# nogamy-build-pipeline — Azure Data Factory

Read when `_context/platform.md` §2 names Azure Data Factory (or Synapse pipelines, where noted). Answers the "Platform specifics" topics of `SKILL.md`. A project override goes in `_context/platform.md` §10 → `nogamy-build-pipeline`.

Sibling of `references/fabric.md` (Fabric Data Factory): the activities and the patterns are the same. What differs: Git format, child call, per-environment values, publish. No pack and no core tool for ADF: the AI uses the Azure CLI (`nogamy-dev-workflow` → `references/adf.md`).
Nogamy's ADF methodology in full: `standards/ADF_Best_Practices_Methodology.md`.

## Where and how named

ADF Git integration fixes the layout under its **root folder** (set in the factory's Git configuration; record it in `_context/platform.md` §4). Default here: `etl/adf/`.

```
etl/adf/                                   ADF root folder: only what ADF writes
  pipeline/PL_Sales_Daily_Run.json         one JSON per item, named after the item
  pipeline/PL_<Source_Group>_Master.json
  pipeline/PL_<Source_Group>_To_Bronze.json
  pipeline/GPL_DQA.json
  dataset/  linkedService/  trigger/  integrationRuntime/  factory/
  arm-template-parameters-definition.json  custom ARM parameters (nogamy-deploy)
etl/<project>/README.md                    one line per pipeline, outside the ADF root
```

- verify: the folder names under the root (`pipeline/`, `dataset/`, `linkedService/`, `trigger/`, `factory/`…) and that global parameters are stored in `factory/`. Learn says only that each resource is exported as its own JSON.
- Never add other files inside the ADF root: Learn warns it "could cause resource loading errors". The README lives outside it.
- Layer folders (`00_orchestration`, `01_bronze`, `03_gold`, `_shared`, `TRY`) are the pipeline's `properties.folder.name`, not repo folders.
- Names: `nogamy-naming` (`PL_…`, `GPL_…`). Pipeline name ≤ 140 characters, activity name ≤ 55; no `. + ? / < > * % & :` or space.
- Parameters `P_`, variables `V_`. No `-` in a global or linked-service parameter name.

## Platform specifics

| Topic | Azure Data Factory |
|---|---|
| ETL tool, orchestration tool | ADF pipelines, for both |
| Text format; export and publish | `etl/adf/pipeline/<name>.json` (ADF Git format), saved by Studio to a branch. Reaches a factory by Publish (Studio) or an ARM deployment (`nogamy-deploy`) |
| How a child item is called | `ExecutePipeline` with `waitOnCompletion: true` (default true). The child is referenced **by name** (`referenceName`), so it is safe across environments |
| Per-environment values | global parameters `@pipeline().globalParameters.<name>`; linked-service properties parameterized in the ARM template; secrets in Key Vault (below) |
| Connections | linked services, referenced by name. Secrets: `AzureKeyVaultSecret` reference, never in the JSON. Who creates: a person with Data Factory Contributor; Key Vault access for the factory's identity is an admin's |
| Parallelism limit in a loop | ForEach `isSequential: false`, `batchCount: 5` (ADF default 20, max 50) |
| Default retry and timeout | ADF defaults: `retry: 0`, `retryIntervalInSeconds: 30`, timeout 12 hours (min 10 minutes, max 7 days). Ours: procedure and Copy steps `retry: 0`, `timeout: 0.12:00:00` |
| Schedule | a `ScheduleTrigger` in `trigger/`, on the `00_orchestration` pipeline. In Git; it runs only after it is started |
| By hand in the UI | Git configuration of the DEV factory; self-hosted IR install and key; the Publish click when the classic flow is used (`nogamy-deploy`) |
| Known traps | below |

## Master pattern

Lookup on the config table (`firstRowOnly: false`, `IS_ACTIVE = 1` + group) → ForEach over `@activity('<Lookup>').output.value` → `ExecutePipeline` → child: Copy to `PRE_BRONZE`, gate, merge (`nogamy-bronze-load` → `references/adf.md`).
- Lookup returns at most 5,000 rows and 4 MB. More rows are cut silently to the first 5,000.
- Lookup on a query or procedure must return exactly one result set, or it fails.
- A token or shared lookup: once, before the ForEach. API credentials in a linked service + Key Vault.
- Gate: `ExecutePipeline` → `GPL_DQA`; the next step `dependsOn` it with `Succeeded`.
- Dependency conditions: `Succeeded`, `Failed`, `Skipped`, `Completed`. A `Completed` path runs after a failure too.

## Retry

- Learn: `policy` (retry, timeout) is "only available for execution activities" (Copy, Script, Stored Procedure…). Its own Lookup sample carries one. verify: which control activities accept a `policy` (`ExecutePipeline`, ForEach, Web).
- Retry only a step that is safe to repeat (the config-window update, the merge procedure), with the transient cause written in the README line.

## Limits that shape the design

| Limit | Value | Then |
|---|---|---|
| ForEach inside ForEach or Until | not allowed | the inner loop goes in a child pipeline |
| ForEach items | 100,000 | split by group |
| `SetVariable` in a parallel ForEach | variables are pipeline-wide: iterations overwrite each other | sequential, or move the logic into the child |
| Activities per pipeline (inner ones included) | 120 | split into children |
| Parameters per pipeline | 50 | group them in config |
| Array parameter through `ExecutePipeline` | arrives in the child as a string | verify: the fix in the troubleshoot guide |
| Pipeline object size | 200 KB | split |

## Synapse pipelines

- Same activities and limits (the Learn pages above apply to both).
- verify: global parameters in Synapse; Learn marks that page as ADF only. Use pipeline parameters with defaults set at deployment instead.
- Repo layout and publish differ (`nogamy-deploy` → `references/adf.md`).

## Before you finish (ADF additions)

- [ ] every child called by `ExecutePipeline` with `waitOnCompletion: true`
- [ ] no server, database, URL, key or environment name in a pipeline, dataset or linked service JSON
- [ ] every `globalParameters.<name>` used exists in DEV and in the deployment's parameter overrides
- [ ] no `encryptedCredential` in a linked service JSON (it does not move between factories)
- [ ] README line in `etl/<project>/README.md`

## Sources

- https://learn.microsoft.com/en-us/azure/data-factory/control-flow-for-each-activity
- https://learn.microsoft.com/en-us/azure/data-factory/control-flow-lookup-activity
- https://learn.microsoft.com/en-us/azure/data-factory/control-flow-execute-pipeline-activity
- https://learn.microsoft.com/en-us/azure/data-factory/concepts-pipelines-activities
- https://learn.microsoft.com/en-us/azure/data-factory/author-global-parameters
- https://learn.microsoft.com/en-us/azure/data-factory/store-credentials-in-key-vault
- https://learn.microsoft.com/en-us/azure/data-factory/parameterize-linked-services
- https://learn.microsoft.com/en-us/azure/data-factory/source-control
- https://learn.microsoft.com/en-us/azure/data-factory/continuous-integration-delivery
- https://learn.microsoft.com/en-us/azure/azure-resource-manager/management/azure-subscription-service-limits
