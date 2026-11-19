# nogamy-platform-watch — Apache Airflow

Read when `_context/platform.md` §2 names Apache Airflow (self-hosted, Astronomer, MWAA or Cloud Composer).

## Source

The official docs: airflow.apache.org (release notes and "Upgrading to Airflow 3"), and the managed service's own docs and supported-versions page.
Start of each daily check: the Airflow release notes since the version in `_context/platform.md` §2, and the managed service's supported versions; then each watch-list item.

## Watch list topics

| Topic | Why we watch it |
|---|---|
| Airflow 2 → 3 changes: removed context variables, data intervals for cron schedules, the REST API version, the CLI | DAG code and the AI's DEV loop (`nogamy-build-pipeline`, `nogamy-dev-workflow`) |
| Scheduling: timetables, `catchup` default, assets (datasets) | run order and the bronze window (`nogamy-build-pipeline`, `nogamy-bronze-load`) |
| Dynamic task mapping (`expand`, `expand_kwargs`), task groups, pools | config-driven loads (`nogamy-build-pipeline`) |
| `TriggerDagRunOperator` (`wait_for_completion`, failure handling) | the master/child pattern and the quality gate (`nogamy-build-pipeline`) |
| Providers for the project's database (operators, hooks, connection fields) | how procedures and checks are called (`nogamy-build-pipeline`, `nogamy-qa-checks`) |
| Secrets backends, Variables, Connections | per-environment values; nothing in the DAG file (`nogamy-deploy`) |
| The managed service: supported Airflow versions, how DAGs and requirements are deployed, end of support | promotion and upgrades (`nogamy-deploy`) |
