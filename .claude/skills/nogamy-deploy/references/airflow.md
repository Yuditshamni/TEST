# nogamy-deploy — Apache Airflow

Read when `_context/platform.md` §2 names Apache Airflow (self-hosted, Astronomer, MWAA or Cloud Composer; note where a managed service differs). Answers the "Platform specifics" topics of `SKILL.md` for DAGs. Database migrations and BI follow their own platform's reference. A project override goes in `_context/platform.md` §5 and §10 → `nogamy-deploy`.

**(3.x)** marks what changed in Airflow 3.

## Same files, different environment

- Every environment gets the same DAG files from `main`. Only Variables, Connections and pools differ.
- One Airflow environment per DEV, TEST, PROD. Never one Airflow serving two environments.
- The AI deploys nothing to TEST or PROD. It prepares the deployment note and the checks.

## How DAGs reach an environment

| Hosting | Mechanism | What moves |
|---|---|---|
| self-hosted, Helm chart | git-sync sidecar on a branch or tag (`dags.gitSync.enabled`, `repo`, `branch`, `subPath`); the docs recommend git-sync without persistence | DAG files only |
| self-hosted, Helm chart | DAGs baked into the image (`images.airflow.repository`, `tag`) | DAGs and Python packages; every change is a redeploy |
| self-hosted **(3.x)** | a Dag bundle: `GitDagBundle` in `[dag_processor] dag_bundle_config_list`, `tracking_ref` = the branch or tag, credentials in `git_conn_id` | DAG files; each run records the commit it ran |
| Astronomer | `astro deploy` (image: Dockerfile, packages, plugins) or `astro deploy --dags` (DAGs only); a Git integration maps a branch to a Deployment | per deploy type |
| MWAA | copy to the environment's S3 bucket `dags/` (`aws s3 cp`); synced to the containers every 30 seconds | DAG files; `requirements.txt` and `plugins.zip` live in the same bucket. verify: the environment update they need |
| Cloud Composer | the environment's Cloud Storage bucket `/dags` (`gcloud composer environments storage dags import`); about 1–2 minutes | DAG files. verify: how PyPI packages move |

- `subPath` / the bundle root = `etl/dags`. Never the repo root.
- Never a token inside a bundle's `repo_url`: bundle kwargs are readable through the config API when `expose_config` is on. Use `git_conn_id`.

## Platform specifics — answers

| Topic | DEV → TEST | TEST → PROD |
|---|---|---|
| Mechanism | per hosting (table above); recorded in `_context/platform.md` §5 | same |
| Trigger, and who | merge to `main` / a tag, then the sync or the CI job; a person, never the AI | a person |
| How migrations are applied | `python tools/run_migrations.py` before the DAGs, in number order (`scripts/README.md`) | same |
| How ETL items move | the DAG files, by the mechanism above | same |
| How the BI model and reports move | the BI platform's reference | same |
| Per-environment values | Variables and Connections in that environment's secrets backend (or `AIRFLOW_VAR_*` / `AIRFLOW_CONN_*`); set by an admin | same |
| What the mechanism does not move | Variables, Connections, pools, the paused state, run history; packages (except an image deploy) | same |
| Backup before a risky change; rollback | data: the warehouse's backup. DAGs: re-deploy the previous commit or tag | same |
| Release window, outside approvals | per project (`_context/platform.md` §5) | per project |

## Pre-checks

- No import error in DEV: `airflow dags list-import-errors` is empty.
- Every Variable, Connection and pool a changed DAG uses: listed in the deployment note, by name, and present in the target **before** the deploy (`airflow variables list`, `airflow connections list`, `airflow pools list`: names only, never `--show-values`).
- New Python packages: in the image or the managed service's requirements, deployed first.
- No host, bucket, account or environment name in a DAG file: search `etl/dags/` for them.

## After the deploy

- `airflow dags list-import-errors` in the target is empty.
- A new DAG is paused at creation (`[core] dags_are_paused_at_creation = True`). The person who deployed unpauses it there.
- The test document: the DAG's run state is `success`, and every task state is read (`airflow tasks states-for-dag-run <dag_id> <run_id>`).

## Known traps

- A DAG that uses a Variable or Connection missing in the target fails at run time, or at parse time if read at the top level.
- **(3.x)** The REST API is `/api/v2`; a script written for `/api/v1` breaks on upgrade.
- **(3.x)** The webserver is `airflow api-server`, and `airflow dag-processor` must run on its own.
- MWAA: the S3 bucket needs Block Public Access and versioning on.

## Sources

- https://airflow.apache.org/docs/helm-chart/stable/manage-dag-files.html
- https://airflow.apache.org/docs/apache-airflow/stable/administration-and-deployment/dag-bundles.html
- https://airflow.apache.org/docs/apache-airflow/stable/installation/upgrading_to_airflow3.html
- https://airflow.apache.org/docs/apache-airflow/stable/security/secrets/secrets-backend/index.html
- https://airflow.apache.org/docs/apache-airflow/stable/cli-and-env-variables-ref.html
- https://airflow.apache.org/docs/apache-airflow/stable/configurations-ref.html
- https://www.astronomer.io/docs/astro/deploy-code
- https://docs.aws.amazon.com/mwaa/latest/userguide/configuring-dag-folder.html
- https://docs.cloud.google.com/composer/docs/composer-3/manage-dags
