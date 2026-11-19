# nogamy-bronze-load — Apache Airflow

Read when `_context/platform.md` §2 names Apache Airflow (self-hosted, Astronomer, MWAA or Cloud Composer; note where a managed service differs). Answers the "Platform specifics" topics of `SKILL.md` for bronze loads orchestrated by Airflow. A project override goes in `_context/platform.md` §10 → `nogamy-bronze-load`.

Airflow is the orchestrator, not the database. Merge syntax and type mapping come from the warehouse's own reference (`_context/platform.md` §2). DAG layout: `nogamy-build-pipeline` → `references/airflow.md`. **(3.x)** marks what changed in Airflow 3.

## Platform specifics

| Topic | Airflow |
|---|---|
| How data lands | a task lands one source table in the staging table (truncated first): the warehouse's bulk load, or a provider transfer operator. Then a `SQLExecuteQueryOperator` task calls the bronze merge procedure. verify: the transfer operator for each source/target pair |
| Where the ETL columns are filled | in the source query or the merge procedure, never in Python inside the task |
| Merge syntax and limits; NULL-safe comparison | the warehouse's (`nogamy-write-sql`); Airflow adds nothing |
| Safety overlap; guard thresholds | from the config row, as in `SKILL.md`; Airflow adds nothing |
| Type mapping per source engine | `sources/<system>/README.md` |
| Errors seen while loading | `nogamy-troubleshoot` → `references/airflow.md` |

## The window: config, not the data interval

The config row (`LAST_TO_DELTA` − overlap … load start) stays the source of truth. Airflow's data interval is not used for it by default.

| Why | Fact |
|---|---|
| the window must not advance when the gate fails | Airflow moves to the next interval whatever bronze holds |
| **(3.x)** a cron string has no interval | `[scheduler] create_cron_data_intervals = False`: `CronTriggerTimetable`, `data_interval_start` = `data_interval_end` = trigger time. In 2.x the default was `True` |
| a manual run | its data interval is not derived from its `logical_date` |
| a run started by an Asset | no logical date, so no `ds` / `ts` |

- The master reads the window with the config rows and passes `from` / `to` to each child as parameters.
- `to` = when the load started, taken in the database (UTC), not `datetime.now()` in Python.

## When a source is partitioned by date (files, daily extracts)

- Then the data interval may be the window: `{{ data_interval_start }}`, `{{ data_interval_end }}` in the SQL template.
- **(3.x)** Needs a timetable with intervals: `CronDataIntervalTimetable`, or `create_cron_data_intervals = True`. Record the choice in `_context/platform.md` §10.
- Past windows: `airflow backfill create --dag-id <id> --from-date … --to-date …` **(3.x)**; `airflow dags backfill <id> -s … -e …` in 2.x.
- **(3.x)** Removed from the context: `execution_date`, `next_ds`, `prev_ds`, `yesterday_ds`, `tomorrow_ds`. Use `data_interval_*`, `logical_date`, `prev_data_interval_end_success`.

## Idempotency

- A cleared task runs again with the same parameters (`try_number` + 1). The same window → the same bronze rows (`SKILL.md`).
- Land = truncate staging + insert; never append to staging.
- Merge by key; never `INSERT` alone into bronze.
- `advance_window` runs last in the child, after `dqa_bronze`, and is safe to repeat.
- `max_active_runs=1` on the master: two runs never load the same table at once.
- Clearing one mapped child: clear that map index only, not the whole map.

## The gate in the DAG

```
land_staging → dqa_staging (Duplicates) → merge_bronze → dqa_bronze (Empty_Table) → advance_window
```

- Each gate is a task that fails on FAIL (the gate procedure raises, or `SQLCheckOperator`). Default trigger rule `all_success`: nothing after a failed gate runs, and the window does not move.
- One failed child must not stop the other children. The task after the map uses a trigger rule that waits for all and then reports the failures (verify: `all_done` and how a failed map index is reported in the run's state).
- The mass-delete guard is in the merge procedure, not in Python.

## Never

- Rows through XCom. XCom carries config rows, counts and ids only.
- `Variable.get` or a database call at the top of the DAG file.
- A source credential in the DAG file or in a Variable value; it is a Connection in the secrets backend.

## Sources

- https://airflow.apache.org/docs/apache-airflow/stable/installation/upgrading_to_airflow3.html
- https://airflow.apache.org/docs/apache-airflow/stable/core-concepts/dag-run.html
- https://airflow.apache.org/docs/apache-airflow/stable/templates-ref.html
- https://airflow.apache.org/docs/apache-airflow/stable/best-practices.html
- https://airflow.apache.org/docs/apache-airflow/stable/configurations-ref.html
- https://airflow.apache.org/docs/apache-airflow/2.10.5/configurations-ref.html
- https://airflow.apache.org/docs/apache-airflow/2.10.5/cli-and-env-variables-ref.html
- https://airflow.apache.org/docs/apache-airflow/stable/core-concepts/tasks.html
- https://airflow.apache.org/docs/apache-airflow-providers-common-sql/stable/operators.html
