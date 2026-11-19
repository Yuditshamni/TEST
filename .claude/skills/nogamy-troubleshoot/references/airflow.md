# nogamy-troubleshoot — Apache Airflow

Read when `_context/platform.md` §2 names Apache Airflow (self-hosted, Astronomer, MWAA or Cloud Composer; note where a managed service differs). Database errors follow the warehouse's reference. A cause met only in this project goes to `_context/platform.md` §10 → `nogamy-troubleshoot`.

**(3.x)** marks what changed in Airflow 3.

## 1. Get the facts

- The DAG parses: `airflow dags list-import-errors`, or `GET /api/v2/importErrors` **(3.x)**. Locally: `python <dag file>.py` must run clean.
- The run: state of the run and of **every** task, mapped indexes too (`nogamy-dev-workflow` → `references/airflow.md`).
- The failed task's log, per try: `GET .../taskInstances/{task_id}/logs/{try_number}`; on disk under `[logging] base_log_folder` (default `{AIRFLOW_HOME}/logs`). With `[logging] remote_logging = True` the log is in the remote store. verify: the log service of MWAA and Cloud Composer.
- One task alone, without recording state: `airflow tasks test <dag_id> <task_id> <date_or_run_id>`.
- The SQL the task ran: run it alone in the database, with the same parameters.
- At L0 or L1: ask for the import-error text or the failed task's log lines around the error, one at a time.

## 2. Known causes on Airflow

| Symptom | Usual cause | Fix |
|---|---|---|
| DAG missing from the list | import error; file without the words `airflow` and `dag`; excluded by `.airflowignore`; the DAG built inside a function | read the import error; assign the DAG at module level |
| the import error says the file timed out | slow top-level code: `Variable.get`, a database call, a heavy import (`[core] dagbag_import_timeout` 30 s, `[dag_processor] dag_file_processor_timeout` 50 s) | templates instead; imports inside the task |
| `ModuleNotFoundError` in the import error | the package is not in DEV's image or requirements | add it there first (`nogamy-deploy`) |
| triggered run stays `queued` | the DAG is paused (new DAGs start paused) | unpause in DEV |
| no new DAGs appear at all **(3.x)** | the DAG processor is not running: it is a separate process | `airflow dag-processor` must run |
| task failed with `AirflowTaskTimeout` | over `execution_timeout` | find the slow step in the database; raise the timeout only with a reason |
| task marked failed with no error in its log (a "zombie") | the worker died or lost its heartbeat. **(3.x)** "task instance heartbeat timeout": `[scheduler] task_instance_heartbeat_timeout` 300 s. 2.x: `scheduler_zombie_task_threshold` 300 s | check the worker's memory and restarts; the task must be safe to repeat |
| a Connection or Variable not found (verify: the exact error text) | not set in this environment, or a name typo | an admin adds it there; same name in every environment |
| a mapped task fails before it runs | the upstream list is longer than `[core] max_map_length` (1024), or not a list or dict | split the config group |
| a run started by an Asset fails on `ds` / `logical_date` | an asset-triggered run has no logical date | use `dag_run.run_id` and the config window |
| `KeyError: 'execution_date'` after the upgrade **(3.x)** | removed context keys (`execution_date`, `next_ds`, `prev_ds`, …) | `logical_date`, `data_interval_*` |
| `xcom_pull()` returns nothing after the upgrade **(3.x)** | without `task_ids` it reads only the current task | pass `task_ids` |
| a task that read the metadata database fails **(3.x)** | direct database access from tasks is removed | the REST API or the Python client |
| `422` on `POST .../dagRuns` **(3.x)** | the body has no `logical_date` key | send `"logical_date": null` |
| a `/api/v1` script fails **(3.x)** | replaced by `/api/v2`, with a JWT from `/auth/token` | update the script |
| the run succeeded, the table is empty | a gate task skipped, or a lenient trigger rule after a failed child | read every task's state; gates use `all_success` |
| two runs moved the same window | `max_active_runs` above 1, or a backfill alongside the schedule | `max_active_runs=1` (`nogamy-build-pipeline`) |

## Sources

- https://airflow.apache.org/docs/apache-airflow/stable/core-concepts/tasks.html
- https://airflow.apache.org/docs/apache-airflow/stable/core-concepts/dags.html
- https://airflow.apache.org/docs/apache-airflow/stable/best-practices.html
- https://airflow.apache.org/docs/apache-airflow/stable/configurations-ref.html
- https://airflow.apache.org/docs/apache-airflow/2.10.5/configurations-ref.html
- https://airflow.apache.org/docs/apache-airflow/stable/cli-and-env-variables-ref.html
- https://airflow.apache.org/docs/apache-airflow/stable/installation/upgrading_to_airflow3.html
- https://airflow.apache.org/docs/apache-airflow/stable/authoring-and-scheduling/dynamic-task-mapping.html
- https://airflow.apache.org/docs/apache-airflow/stable/templates-ref.html
- https://airflow.apache.org/docs/apache-airflow/stable/security/api.html
- https://www.astronomer.io/docs/astro/airflow-api
