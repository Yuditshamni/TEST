# nogamy-build-pipeline — Apache Airflow

Read when `_context/platform.md` §2 names Apache Airflow (self-hosted, Astronomer, MWAA or Cloud Composer; note where a managed service differs). Answers the "Platform specifics" topics of `SKILL.md` for Airflow DAGs. A project override goes in `_context/platform.md` §10 → `nogamy-build-pipeline`.

Targets Airflow 2.x and 3.x. **(3.x)** marks what changed in Airflow 3. Checked against the 3.4.0 docs.

## Where and how named

```
etl/dags/                                   the folder Airflow reads (dags folder or Dag bundle root)
  <project>/
    00_orchestration/PL_Sales_Daily_Run.py   the only DAG with a schedule; triggers and waits
    01_bronze/PL_<Source_Group>_Master.py    reads config, maps the child over the rows
    03_gold/PL_Run_Sales_Gold.py             dims → facts with quality gates
    README.md                                one line per DAG
  _shared/                                   shared Python (callables, task groups), no DAG
  .airflowignore                             excludes folders that hold no DAG
```

- One DAG per file. File name = `dag_id` + `.py`. `dag_id` follows `nogamy-naming` (`PL_<Action>_<Domain>_<Layer>`).
- `task_id`: what the step does, lowercase with underscores (`read_config`, `load_bronze`, `dqa_bronze`, `advance_window`). Same ids in every environment. In a task group it gets the `group_id` as prefix: keep it, never `prefix_group_id=False`.
- verify: the allowed characters and maximum length of `dag_id` and `task_id`.

## Platform specifics

| Topic | Airflow |
|---|---|
| ETL tool, orchestration tool | Airflow orchestrates. Data moves in the database (procedures) or through a provider's transfer operator (`nogamy-bronze-load` → `references/airflow.md`) |
| Text format; export and publish | the DAG is a Python file, already text. Publish = the file reaches the environment's dags folder or Dag bundle (`nogamy-deploy` → `references/airflow.md`) |
| How a child item is called | inside a DAG: a task group mapped over the config rows. Across DAGs: `TriggerDagRunOperator` with `wait_for_completion=True`, by `dag_id` (below) |
| Per-environment values | Airflow Variables and Connections, read by name; values come from the environment (secrets backend, `AIRFLOW_VAR_*` / `AIRFLOW_CONN_*`, metastore) |
| Connections | by `conn_id`, the same id in every environment. Created by an admin in each environment, never by the AI, never in the DAG file |
| Parallelism limit in a loop | a pool per source group (`pool=`, 5 slots by default here), or `max_active_tis_per_dag` on a mapped task |
| Default retry and timeout | `retries=0`, `execution_timeout=timedelta(hours=12)` on load tasks: investigate, do not retry. Safe to repeat: `advance_window` (shared config table) and the bronze merge, `retries=2`, `retry_delay=timedelta(seconds=30)`. Over the timeout: `AirflowTaskTimeout`. Airflow's default: `[core] default_task_retries = 0`, no timeout |
| Schedule | `schedule=` in the `00_orchestration` DAG file, so it is in Git. Every other DAG: `schedule=None`. Every DAG: `catchup=False` written out (default `True` in 2.x, `False` in **3.x**), `max_active_runs=1` (one window at a time) |
| By hand in the UI | creating Connections and pools; unpausing a new DAG in TEST and PROD |
| Known traps | below |

## Master and child

| Need | Use |
|---|---|
| orchestration DAG → domain DAG | `TriggerDagRunOperator(trigger_dag_id=..., wait_for_completion=True, conf={...})` (Airflow 3: `airflow.providers.standard.operators.trigger_dagrun`) |
| master → one child per config row | `read_config` task returns the active rows (`IS_ACTIVE = 1`) → a `@task_group` child called with `.expand_kwargs(rows)`; at most `[core] max_map_length` rows (default 1024) |
| child: one source table | the task group: land → gate on staging → merge → gate on bronze → advance window. It gets parameters, never reads the config table |
| run one child alone | a small DAG with `schedule=None` that calls the same task group with `params`, or `airflow tasks test` with `--map-index` |
| dims → facts | tasks in parallel → an `EmptyOperator` `finish_dims` → dims gate → facts → `finish_facts` → facts gate |

- Not the default: Assets **(3.x; Datasets in 2.x)**. An asset-triggered run has no logical date, and the caller cannot wait or gate on it. SubDAGs: removed in 3.x, never.

## Calling a procedure

```python
SQLExecuteQueryOperator(
    task_id="load_bronze",
    conn_id="dwh",                      # same id in every environment
    sql="sql/load_bronze.sql",          # or a string; .sql files are templates
    parameters={"system": "{{ params.system }}"},
    autocommit=True,
)
```

- Import: `airflow.providers.common.sql.operators.sql`. The database's provider package must be installed (e.g. `apache-airflow-providers-microsoft-mssql`, `-postgres`, `-snowflake`).
- Procedure syntax (`EXEC`, `CALL`) and parameter style follow the driver: `nogamy-write-sql`. verify: the parameter placeholder of the project's driver.
- Quality gate: the project's gate procedure through the same operator (it raises on FAIL), or `SQLCheckOperator` (fails when any value of the first row is falsy).

## Known traps

- Top-level code runs at every parse: no `Variable.get`, no database call, no network at the top of the file. Use templates (`{{ var.value.x }}`, `{{ conn.x.host }}`), read at run time.
- **(3.x)** Task code can no longer reach the metadata database. Use the REST API or the Python client.
- **(3.x)** `xcom_pull()` without `task_ids` reads only the current task. Always pass `task_ids`.
- **(3.x)** Imports move to `airflow.sdk` (`dag`, `task`, `task_group`, `DAG`, `Variable`, `Asset`). The old paths warn from 3.1.
- **(3.x)** `BashOperator`, `PythonOperator`, `TriggerDagRunOperator`, `ExternalTaskSensor` are in `apache-airflow-providers-standard`. It installs on 2.x too.
- **(3.x)** `schedule=` only: `schedule_interval` and `timetable` were removed. SLAs too (Deadline Alerts, 3.1).
- A new DAG is paused at creation (`[core] dags_are_paused_at_creation = True`). A triggered run of a paused DAG stays queued.

## Before you finish (Airflow additions)

- [ ] `python etl/dags/<project>/<layer>/<dag_id>.py` runs clean; no import error in DEV
- [ ] `catchup=False`, `max_active_runs=1`, `schedule=None` except the orchestration DAG
- [ ] no host, path, account or environment name in the file; Variables and Connections by name only
- [ ] every Variable, Connection and pool the DAG uses exists in DEV, and is in the deployment note
- [ ] README line in `etl/dags/<project>/README.md`

## Sources

- https://airflow.apache.org/docs/apache-airflow/stable/installation/upgrading_to_airflow3.html
- https://airflow.apache.org/docs/apache-airflow/stable/core-concepts/dags.html
- https://airflow.apache.org/docs/apache-airflow/stable/core-concepts/tasks.html
- https://airflow.apache.org/docs/apache-airflow/stable/core-concepts/dag-run.html
- https://airflow.apache.org/docs/apache-airflow/stable/authoring-and-scheduling/dynamic-task-mapping.html
- https://airflow.apache.org/docs/apache-airflow/stable/authoring-and-scheduling/asset-scheduling.html
- https://airflow.apache.org/docs/apache-airflow/stable/administration-and-deployment/pools.html
- https://airflow.apache.org/docs/apache-airflow/stable/best-practices.html
- https://airflow.apache.org/docs/apache-airflow/stable/configurations-ref.html
- https://airflow.apache.org/docs/apache-airflow/2.10.5/configurations-ref.html
- https://airflow.apache.org/docs/apache-airflow-providers-common-sql/stable/_api/airflow/providers/common/sql/operators/sql/index.html
- https://airflow.apache.org/docs/apache-airflow-providers-standard/stable/_api/airflow/providers/standard/operators/trigger_dagrun/index.html
- https://airflow.apache.org/docs/apache-airflow/3.0.0/release_notes.html
