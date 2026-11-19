# nogamy-git-workflow — Apache Airflow

Read when `_context/platform.md` §2 names Apache Airflow (self-hosted, Astronomer, MWAA or Cloud Composer; note where a managed service differs). Answers the Airflow topics of "Platform specifics" in `SKILL.md`. Provider, approvers and who merges stay in `_context/platform.md` §4 and `PROJECT.md`. A project override goes in `_context/platform.md` §10 → `nogamy-git-workflow`.

**(3.x)** marks what changed in Airflow 3.

## Git is the source; Airflow reads from it

- A DAG is a Python file written in the repo. There is no export from the tool.
- Never edit a DAG on a server, a bucket or a mounted folder. Change the file in the branch, then publish.
- The flow: topic branch → files → publish to DEV, run (`nogamy-dev-workflow`) → commit → PR → a person merges → the environment picks up `main` (`nogamy-deploy`).

## Platform specifics — answers

| Topic | Airflow |
|---|---|
| May the AI push or open a PR? | no (default). A DEV that syncs from a branch then waits for the developer's push |
| Platform ↔ Git sync | Git → Airflow only: git-sync (Helm chart), a `GitDagBundle` **(3.x)**, Astronomer's Git integration, or a CI job that copies to the MWAA / Composer bucket. Never Airflow → Git |
| Tool → file | none: the file is the definition |
| File → tool | the sync or the copy above; `tracking_ref` / branch per environment, recorded in `_context/platform.md` §4 |
| Text formats in the repo | DAGs: `.py` under `etl/dags/`; SQL they run: `.sql` under `db/` or next to the DAG; dependencies: `requirements.txt` or the image `Dockerfile`; `.airflowignore` |
| Not in Git, and where it is recorded | Connections, Variables' values, pools, the paused state, run history and logs. Their **names** go in the deployment note and `etl/dags/<project>/README.md` |

## What never enters Git

- Connection URIs, passwords, tokens, keys; `AIRFLOW_CONN_*` values; files of Connections or Variables made for `airflow connections import` / `airflow variables import`.
- `airflow.cfg` with secrets, `.env` files, `logs/`, `__pycache__/`.
- A Variable value that differs per environment. Its name and meaning: yes, in the README.

## Version per run

- **(3.x)** With a `GitDagBundle` each run records the commit it was created with, and a re-run uses the same code. In the PR, name the commit that ran in DEV.
- 2.x, or a bundle without versioning (local, S3, GCS): a re-run uses whatever file is deployed now.

## Commit and PR (Airflow additions)

- [ ] one DAG per file; `dag_id` = file name; ids unchanged unless the PR says so (a new `dag_id` starts with no history and paused)
- [ ] new Variables, Connections, pools and packages listed in the PR for the admin
- [ ] the DEV run id and every task's state pasted in the PR

## Sources

- https://airflow.apache.org/docs/apache-airflow/stable/administration-and-deployment/dag-bundles.html
- https://airflow.apache.org/docs/helm-chart/stable/manage-dag-files.html
- https://airflow.apache.org/docs/apache-airflow/stable/configurations-ref.html
- https://www.astronomer.io/docs/astro/deploy-code
- https://docs.aws.amazon.com/mwaa/latest/userguide/configuring-dag-folder.html
- https://docs.cloud.google.com/composer/docs/composer-3/manage-dags
