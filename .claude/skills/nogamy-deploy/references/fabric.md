# nogamy-deploy — Microsoft Fabric

Read when `_context/platform.md` §2 names Microsoft Fabric.

Needs the Fabric pack (`tools/fabric/`, `tools/migrate/`, `PROJECT.md` → `Packs: fabric`). Missing → `nogamy-add-pack` first.

## The core's Fabric path: CI/CD runner

The default with the Fabric pack: a CI/CD runner (GitHub Actions; workflow files in `PROJECT.md` → DevOps) deploys from `main`. **No manual deploy, no Fabric Deployment pipeline.** The project records any other choice in `_context/platform.md` §5.

| What | How |
|---|---|
| Warehouse `WH_DWH` (tables, views, procedures, functions) | numbered migrations, `tools/migrate/run_migrations.py`, in number order (`scripts/README.md`), first |
| Pipelines, Variable library, semantic models, reports | the same run, after the migrations |

| Move | Trigger | When |
|---|---|---|
| → TEST | automatic, no AI | CI passed on `main` |
| → PROD | a deliberate click by a person, no AI (who: `PROJECT.md` → People and roles) | after the TEST checks pass |

Order: PR → the repo's CI green → merge to `main` → the runner deploys to TEST, then PROD on the click. DEV is filled by the agent from the branch (`nogamy-dev-workflow`).

## Test document on Fabric

- Section 1: the migration log row has `IS_EXECUTED = 1` and no `ERROR_MSG`.
- Section 4: the pipeline's expected status is `Succeeded`; the data-quality groups (`GPL_DQA`) pass.
- TEST: the developer runs the document after the runner's deploy and fills the `TEST` column (the agent has no access). PROD: whoever clicked runs sections 1 and 3.

## Pre-checks on Fabric

- DEV at the last migration: `python tools/migrate/run_migrations.py <DEV endpoint> --dry-run` shows nothing pending.
- Repo and DEV agree: `python tools/fabric/drift_check.py <DEV workspace> fabric/data <server>`.
- No hard-coded IDs in a pipeline: search the `pipeline-content.json` files for GUIDs and for `datawarehouse.fabric.microsoft.com`.

## After the deploy

- Check the run in GitHub Actions, step by step; compare `MNG.MNG_MIGRATION_LOG` in the target with the deployment note.
- Seed and grants: run them if the runner does not (confirm per project, `_context/open-questions.md`).

## Facts to remember

- IDs inside pipelines come from the Variable library (`VL_DWH`), never typed into the JSON.
- **Before the first promotion to a workspace:** a value set for it in `VL_DWH`, set as active there; a workspace identity with a role in that workspace; a `FabricDataPipelines` connection on that identity, its ID in the runner's connections. Without them child pipelines do not run.
- The agent's service principal is for the DEV workspace only (`PROJECT.md` → Environments).
- Direct Lake models do not rebind to the target warehouse by themselves: they need a data source rule.
- Backup before a risky PROD change: `CREATE TABLE ... AS SELECT` into a dated copy, or a warehouse restore point.

## Platform specifics — answers

| Topic | DEV → TEST | TEST → PROD |
|---|---|---|
| Mechanism | CI/CD (GitHub Actions runner) | CI/CD (GitHub Actions runner) |
| Trigger, and who | automatic after CI on `main` | a deliberate click by a person |
| How migrations are applied | `tools/migrate/run_migrations.py`, number order, first | same |
| How ETL items move | the runner publishes the pipelines and the Variable library | same |
| How the BI model and reports move | the runner, after the pipelines | same |
| Per-environment values | Variable library `VL_DWH`, a value set per workspace, active there | same |
| What the mechanism does not move | data; seed and grants unless the runner runs them (confirm per project) | same |
| Backup before a risky change; rollback | CTAS dated copy or a restore point | same |
| Release window, outside approvals | per project (`_context/platform.md` §5) | per project |

Known traps: child pipelines fail on a workspace without the Variable library value, identity and `FabricDataPipelines` connection; Direct Lake models keep pointing at DEV without a data source rule.
