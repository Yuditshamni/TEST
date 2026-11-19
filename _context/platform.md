# platform.md — the project's platform profile

status: not set up

Filled by the `nogamy-project-setup` skill. The technical profile of the project; a platform fact is changed **only here**.
Identity, environment names, people and packs: `PROJECT.md`. Platform knowledge shipped by the core: `references/<platform>.md` in each skill.
`?` = not answered yet. A `?` that blocks work is also a row in `open-questions.md`, with an owner.
No secrets in this file: names and addresses only, never passwords, keys or tokens.

## 1. Project

| Topic | Value |
|---|---|
| Client, scope, legacy system, people | `PROJECT.md` |
| What is built, first deliverable | ? |
| Language of business values (descriptions, synonyms, rules) | Hebrew |

## 2. Stack

| Topic | Value |
|---|---|
| Database / warehouse engine, version | ? |
| Platform references shipped by the core that apply (`references/<platform>.md` in the skills: `fabric`, `sqlserver`, `adf`, `airflow`; one or more, e.g. `sqlserver, adf`), or "none" | ? |
| SQL dialect, and what it lacks (see `nogamy-write-sql`) | ? |
| Case sensitivity of names and of data | ? |
| Ingestion / ETL tool | ? |
| Orchestration and scheduling | ? |
| Transformation: SQL procedures (method default) or another tool | ? |
| BI tool and semantic layer | ? |
| Official documentation (the only source for platform facts) | ? |

## 3. Environments

Names: `PROJECT.md` → Environments (one place).

| Environment | Data: real / masked / test | Who can change it |
|---|---|---|
| DEV | ? | ? |
| TEST | ? | ? |
| PROD | ? | ? |

Fewer or more environments: change the rows. A project with no separate DEV says so here, and the AI then works at L0.

## 4. Code and Git

| Topic | Value |
|---|---|
| Git provider and repo address | ? |
| How the repo is reached (VPN, IP allow list, account) | ? |
| Main branch; protected? | ? |
| Branch model | topic branches: `feature/<what>`, `stt/<what>`, `context/<topic>` |
| Review path: who approves a PR; automatic checks (CI) | ? |
| Who commits · who pushes · who opens a PR | AI commits only when asked, never pushes; a person pushes and opens the PR |
| Does the platform sync with Git by itself? usable here? | ? |
| If not: how a definition gets from the tool into a file, and back | ? |
| Kept as text in Git | database objects: ? · ETL items: ? · BI model: ? · reports: ? |
| Cannot be kept in Git (connections, permissions, schedules…) and where it is recorded | ? |

## 5. Promotion between environments

| Hop | Mechanism | Trigger | Who |
|---|---|---|---|
| → DEV | ? | ? | ? |
| DEV → TEST | ? | ? | ? |
| TEST → PROD | ? | ? | ? |

Mechanism is one of: **manual** (a person runs the scripts in order, from the deployment note) · **platform tool** (the platform's own deployment feature) · **CI/CD** (a pipeline or runner that deploys from the main branch).

| What moves | How |
|---|---|
| Database objects | ? (default: numbered migrations, §6) |
| ETL / orchestration items | ? |
| BI models and reports | ? |
| Config rows, grants | ? (default: `scripts/seed/`, `scripts/grants/`, after the migrations) |
| Values that differ per environment (connections, IDs, paths) | ? (a parameter file, a variable set, a config table; never typed into code) |
| Order | database first, then the items that call it |
| Backup before a risky PROD change | ? |
| Rollback | ? |
| Evidence kept | deployment note in the PR, test document in `qa/deploy/`, migration log |

## 6. Database change model

| Topic | Value |
|---|---|
| Model | object file (current state) + numbered migration per change (method default) / state-based compare tool / other: ? |
| Migration runner | ? (default: `tools/run_migrations.py` with a profile in `_private/db-profiles.json` / its `--run-sheet` for a person / the project's own migration tool) |
| Migration log table | `MNG.MNG_MIGRATION_LOG` |
| Idempotent guard in this dialect | ? (`scripts/README.md`) |

## 7. AI access

| Topic | Value |
|---|---|
| Approved AI tool(s) | ? |
| Access level (`AGENTS.md`: L0 files only · L1 SQL read · L2 SQL write · L3 full loop) | L0 until answered |
| Identity the AI runs as, and its role | ? |
| Environments it reaches | DEV only |
| How a query is run (the exact command or tool) | ? |
| How an ETL item is published and run (L3) | ? |
| Approvals pending (information security, licences) | ? |
| Proof the access works (one harmless query, with its result) | ? |

## 8. Data sensitivity

| Topic | Value |
|---|---|
| Sensitive data in scope (personal, financial, medical…) | ? |
| What the AI may read | structure, counts, sums; values only of columns marked `pii: no` |
| DEV data | ? (test / masked / real) |
| Rules from the client (regulation, security policy) | ? |

## 9. Platform skills status

Skills are core and read-only here. A platform skill is ready when its `Platform specifics` questions are answered:
by the core reference for this platform (`references/<platform>.md` in the skill folder), by §10 below, or both.

| Skill | Covered by |
|---|---|
| `nogamy-dev-workflow` | ? |
| `nogamy-git-workflow` | ? |
| `nogamy-deploy` | ? |
| `nogamy-write-sql` | ? |
| `nogamy-db-objects` | ? |
| `nogamy-bronze-load` | ? |
| `nogamy-build-pipeline` | ? |
| `nogamy-semantic-model` | ? |

Covered by: `core reference (<platform>)` · `§10` · `core reference + §10` · `not used`. Still `?` → the skill works from its question list; answer it in §10.

## 10. Platform notes per skill

What this project adds to, or overrides in, a skill's platform facts. Same topics as the skill's `Platform specifics` table.
Only what differs from the core reference. A fact every project on this platform needs → `nogamy-feedback`, so it enters the core reference.

### nogamy-write-sql

| Topic | This project |
|---|---|

### nogamy-db-objects

| Topic | This project |
|---|---|

<Add a heading per skill only when there is something to say.>
