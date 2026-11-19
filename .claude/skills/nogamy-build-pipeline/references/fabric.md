# nogamy-build-pipeline — Microsoft Fabric

Read when `_context/platform.md` §2 names Fabric. Answers the "Platform specifics" topics of `SKILL.md` for Fabric Data Factory pipelines (`pipeline-content.json`). A project override goes in `_context/platform.md` §10 → `nogamy-build-pipeline`.

Needs the Fabric pack (`tools/fabric/`, `tools/migrate/`, `PROJECT.md` → `Packs: fabric`). Missing → run `nogamy-add-pack` first.

## Where and how named

```
fabric/data/pipelines/<project>/
  00_orchestration/PL_Sales_Daily_Run.DataPipeline/          schedule; Invoke Pipeline + Wait only
  01_bronze/PL_Run_Sales_Bronze.DataPipeline/                domain bronze wrapper
  01_bronze/PL_<Source_Group>_Master.DataPipeline/           reads config, drives the ForEach
  01_bronze/PL_<Source_Group>_To_Bronze.DataPipeline/        child: one source table
  03_gold/PL_Run_Sales_Gold.DataPipeline/                    dims → facts with DQA gates
  README.md                                                  one line per pipeline
fabric/data/pipelines/_shared/GPL_DQA.DataPipeline/
fabric/data/pipelines/_shared/VL_DWH.VariableLibrary/
```

- Every parameter that has a sensible default gets a `defaultValue`.
- Try-out pipeline: workspace folder `pipelines/TRY`, never the workspace root or a project folder.

## Platform specifics

| Topic | Fabric |
|---|---|
| ETL tool, orchestration tool | Fabric Data Factory pipelines, for both |
| Text format; export and publish | `<name>.DataPipeline/pipeline-content.json` (Fabric Git format). Published by the AI with `tools/fabric/publish_pipeline.py` (below) |
| How a child item is called | `InvokePipeline` with `waitOnCompletion: true`. Never the legacy `ExecutePipeline`: it types the DEV pipeline GUID into the JSON |
| Per-environment values | the Variable library `VL_DWH` in `pipelines/_shared` (below) |
| Connections | by connection ID, through a placeholder in the JSON; real IDs in `_private/fabric_agent.json`, per workspace |
| Parallelism limit in a loop | ForEach `isSequential: false`, `batchCount: 5` |
| Default retry and timeout | procedure activities `retry: 0`, `timeout: 0.12:00:00`; exceptions below |
| Schedule | on the `00_orchestration` pipeline |
| By hand in the UI | nothing for publishing; creating a connection credential with OAuth2 (portal only) |
| Known traps | below |

## Master pattern (base ADF methodology)

Lookup on `MNG.MNG_BRONZE_CONFIGURATION` (`firstRowOnly: false`, `IS_ACTIVE = 1` + group) → ForEach → `InvokePipeline` → child: Copy activity to `PRE_BRONZE` / `BRONZE` (`nogamy-bronze-load` → `references/fabric.md`).

- Window: from config (`LAST_TO_DELTA` − 1 day … now). A special-dates table overrides it (`IS_DONE = 0` → use it, then set `1`).
- Script activities: type `Query` for a procedure that runs a load (it returns the row counts); `NonQuery` for an `UPDATE` / `INSERT`.
- API sources: a Web activity gets the token once, before the ForEach; credentials in a Fabric connection, never in the JSON. Prove the call first (e.g. in Postman), then build.
- Gold order: dims in parallel → `Finish Dims` → dims DQA → facts → `Finish Facts` → facts DQA. A fact that depends on another fact lists it in `dependsOn`.

## Retry

- Load activities: `retry: 0`. Failures are investigated, not retried.
- Updates on a table shared by parallel children (e.g. `Update_Config_Window`): `retry: 3`, `retryIntervalInSeconds: 30`. Fabric detects write conflicts per table, also on different rows (Microsoft Learn, error 24556), so a healthy table can fail by timing. The update must be safe to repeat.
- `BRONZE.SP_LOAD_BRONZE_<SYSTEM>`: `retry: 2`, `retryIntervalInSeconds: 30`: safe to repeat, and `MERGE` can hit a write conflict with compaction.

## No hard-coded environment: the Variable library

IDs of workspace, warehouse, SQL endpoint and child pipelines are **never** hard-coded. Take them from `VL_DWH` (variable type String):

```json
"linkedService": {
  "name": "WH_DWH",
  "properties": {
    "type": "DataWarehouse",
    "typeProperties": {
      "endpoint":    "@pipeline().libraryVariables.WH_DWH_endpoint",
      "artifactId":  "@pipeline().libraryVariables.WH_DWH_id",
      "workspaceId": "@pipeline().libraryVariables.data_workspace_id"
    }
  }
}
```

Every variable a pipeline uses is declared under `properties`. Microsoft Learn does not document this format; Fabric accepts and keeps it:

```json
"libraryVariables": {
  "WH_DWH_id": { "type": "String", "variableName": "WH_DWH_id", "libraryName": "VL_DWH" }
}
```

## Child pipelines and connections

- `InvokePipeline` calls the Fabric API, so it needs a connection of type `FabricDataPipelines`, in the JSON as the placeholder `__FABRIC_PIPELINES_CONNECTION__`.
- Credential: `POST /connections` accepts `ServicePrincipal` and `WorkspaceIdentity`. `OAuth2` is refused (`OAuthNotSupportedForConnection`); it works only in the portal.
- A `WorkspaceIdentity` connection can be created while the workspace has no identity; the run then fails with `Failed to get Workspace Identity access token`. The identity is created without a role: it needs a role in the workspace. Right after the role is given, a child can fail with `Job failed to start: unable to acquire user token`; the same run passed about 35 minutes later. Creating it and giving the role are permission changes, for a workspace admin, not the AI.

## Publish and test

1. `publish_pipeline.py` creates the pipeline when it is missing, in the workspace folder that mirrors the repo (`pipelines/<project>/<NN_layer>`, `pipelines/_shared`; a try-out: `pipelines/TRY`). No step in the portal.
2. Variable library first, when it changed: `python tools/fabric/publish_variable_library.py <DEV workspace> fabric/data/pipelines/_shared/VL_DWH.VariableLibrary --as-user`
3. `python tools/fabric/publish_pipeline.py <DEV workspace> fabric/data/pipelines/<project>/<NN_layer>/<name>.DataPipeline --as-user`
4. `python tools/fabric/run_pipeline.py <DEV workspace> <name> [NAME=value ...]`: prints every activity run. Then the table checks. A clean drift check does not prove a pipeline runs.

## Before you finish (Fabric additions)

- [ ] `dependsOn` complete
- [ ] no GUID, endpoint or environment name typed into the JSON
- [ ] every `libraryVariables.<name>` used is declared in `properties.libraryVariables`
- [ ] README line in `fabric/data/pipelines/<project>/README.md`
