# nogamy-dev-workflow — Apache Airflow

Read when `_context/platform.md` §2 names Apache Airflow (self-hosted, Astronomer, MWAA or Cloud Composer; note where a managed service differs). Answers the "Platform specifics" topics of `SKILL.md` for DAGs. Database steps follow the warehouse's reference. A project override goes in `_context/platform.md` §10 → `nogamy-dev-workflow`.

**(3.x)** marks what changed in Airflow 3.

## The AI's identity in DEV

- One Airflow user or API token for the AI, in the DEV environment only (`PROJECT.md` → Environments). TEST and PROD never get one.
- Its role: trigger, pause/unpause and read runs and logs. Not: edit Connections, Variables or pools, or delete runs.
- The token lives in `_private/`, never in the repo or the chat.
- **(3.x)** The default auth manager is Simple Auth; roles need the FAB provider (`auth_manager = ...FabAuthManager`) or the managed service's own.

## Three ways to reach DEV

| Way | When | How |
|---|---|---|
| REST API | the default for an agent; works with every hosting | **(3.x)** `POST /auth/token` → `access_token`; then `Authorization: Bearer <token>` on `/api/v2/...`. 2.x: `/api/v1`, auth per `[api] auth_backends` (verify: the backend the project enabled) |
| `airflowctl` **(3.x)** | a remote CLI over the API | `airflowctl auth login --api-url <DEV url> --api-token <token>`; headless: `AIRFLOW_CLI_TOKEN` + `--skip-keyring`. verify: the trigger sub-command name (`dagrun trigger` / `dags trigger`) |
| `airflow` CLI | only on a DEV host or container that runs Airflow | `airflow dags ...`, `airflow tasks ...` (below) |

Managed services: Astronomer takes a Deployment / Workspace API token as Bearer. verify: the REST API sign-in for MWAA and Cloud Composer.

## Run a DAG in DEV and read every task

| What | REST **(3.x)** | CLI |
|---|---|---|
| parse check, before the run | `GET /api/v2/importErrors` | `airflow dags list-import-errors` |
| unpause (a new DAG starts paused) | `PATCH /api/v2/dags/{dag_id}` `{"is_paused": false}` | `airflow dags unpause <dag_id>` |
| trigger | `POST /api/v2/dags/{dag_id}/dagRuns` with `{"logical_date": null, "conf": {...}}`; `logical_date` must be present (may be null), else `422` | `airflow dags trigger <dag_id> -c '<json>'` |
| run state | `GET /api/v2/dags/{dag_id}/dagRuns/{dag_run_id}` | `airflow dags state <dag_id> <run_id>` |
| every task's state | `GET /api/v2/dags/{dag_id}/dagRuns/{dag_run_id}/taskInstances` | `airflow tasks states-for-dag-run <dag_id> <run_id>` |
| mapped children | `GET .../taskInstances/{task_id}/listMapped` | — |
| a task's log | `GET .../taskInstances/{task_id}/logs/{try_number}` | the log folder (`[logging] base_log_folder`) |
| re-run failed tasks | `POST /api/v2/dags/{dag_id}/clearTaskInstances` | `airflow tasks clear` (keeps task state); UI: Clear |

- In one process, without the scheduler: `airflow dags test <dag_id> [logical_date] -c '<json>'` (`dag.test()` in Python). It runs real tasks against DEV's Connections.
- One task alone, state not recorded: `airflow tasks test <dag_id> <task_id> [date_or_run_id] [--map-index N]`.
- 2.x: the date argument is `execution_date`; `airflow dags trigger -e`.
- A DAG run can succeed while a task was skipped or a map index failed under a lenient trigger rule. Read every task.

## Publish to DEV

The DAG file must reach DEV's dags folder or bundle (`nogamy-deploy` → `references/airflow.md`), from the topic branch:

| DEV hosting | The AI at L3 runs | Else (run sheet) |
|---|---|---|
| local / Docker DEV | copies the file into the mounted dags folder | — |
| DEV bundle or git-sync on a branch | nothing: it needs a push, and the AI does not push (`nogamy-git-workflow`) | the developer pushes the branch |
| Astronomer | `astro deploy <DEV deployment id> --dags` (verify: the deployment argument) | same, by the developer |
| MWAA | `aws s3 cp <file> s3://<DEV bucket>/dags/<path>` | same |
| Cloud Composer | `gcloud composer environments storage dags import --environment <DEV> --location <region> --source <file>` | same |

Then: wait for the parse, check import errors, unpause, trigger, read every task, then the table checks.

## Platform specifics — answers

| Topic | Airflow |
|---|---|
| Access level | per project (`_context/platform.md` §7); L3 needs a DEV API token and a way to publish DEV |
| Folder layout | `etl/dags/<project>/<NN_layer>/<dag_id>.py`; SQL in `db/` (`nogamy-db-objects`) |
| Run a query / a `.sql` file in DEV | the warehouse's reference; not through Airflow |
| Apply migrations in DEV | `python tools/run_migrations.py ... --as-agent` |
| Publish an ETL item to DEV | table above |
| Run an ETL item and read its steps | table above |
| Compare repo with DEV | `airflow dags list -o json` (`fileloc`, `bundle_version`) against the files in `etl/dags/`; names of Variables and Connections against the deployment note |
| By hand in the UI | Connections, Variables, pools; the AI identity and its role |

## Sources

- https://airflow.apache.org/docs/apache-airflow/stable/security/api.html
- https://airflow.apache.org/docs/apache-airflow/stable/cli-and-env-variables-ref.html
- https://airflow.apache.org/docs/apache-airflow/2.10.5/cli-and-env-variables-ref.html
- https://airflow.apache.org/docs/apache-airflow/2.10.5/configurations-ref.html
- https://airflow.apache.org/docs/apache-airflow/stable/core-concepts/debug.html
- https://airflow.apache.org/docs/apache-airflow/stable/installation/upgrading_to_airflow3.html
- https://airflow.apache.org/docs/apache-airflow-ctl/stable/howto/index.html
- https://github.com/apache/airflow/blob/main/airflow-core/src/airflow/api_fastapi/core_api/openapi/v2-rest-api-generated.yaml
- https://www.astronomer.io/docs/astro/airflow-api
- https://docs.aws.amazon.com/mwaa/latest/userguide/configuring-dag-folder.html
- https://docs.cloud.google.com/composer/docs/composer-3/manage-dags
