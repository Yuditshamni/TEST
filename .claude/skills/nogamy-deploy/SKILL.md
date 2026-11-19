---
name: nogamy-deploy
description: Prepare and check a promotion between environments (DEV → TEST → PROD), whatever the mechanism — a person running scripts by hand, the platform's deployment tool, or a CI/CD pipeline. Deployment note, pre-checks, order of steps, the test document per deploy, what to verify after. The AI prepares and checks; it never promotes. Use after a change is approved, when writing a migration or a test document, and when asked how a change reaches TEST or PROD.
---

# Promotion

The AI **never promotes** and has no access to TEST or PROD. It prepares the deployment note and the test document, and checks DEV. The mechanism of each hop, and who triggers it, are in `_context/platform.md` §5.

## The three mechanisms

| Mechanism | What happens | What the AI prepares |
|---|---|---|
| **manual** | a person runs the scripts in the target, in order | a run sheet: every script and command in order, with the expected result of each (`nogamy-dev-workflow`) |
| **platform tool** | the platform's deployment feature copies definitions | the list of items to select, in order, and what the tool does **not** move (data, grants, config rows, per-environment values) |
| **CI/CD** | a pipeline or runner deploys from the main branch | the deployment note in the PR; nothing is run by hand |

The rules below hold for all three.

## Rules that do not depend on the mechanism

- **From the main branch only.** DEV runs from the branch, before the PR. TEST and PROD get what was merged, never a branch: PR → automatic checks green → merge → deploy.
- **Same definitions everywhere.** Promotion moves definitions, not data. No environment in names or code; values that differ come from the per-environment mechanism.
- **Database first, then what calls it.** An ETL item that calls a new procedure needs that migration first.
- **Order:** migrations (by number) → seed → grants → ETL items → BI model and reports → loads → checks.
- **Every environment keeps a log** of the migrations it ran (`MNG.MNG_MIGRATION_LOG`). Compare the logs when environments differ.
- **PROD is a deliberate act of a person**, after the TEST checks passed.
- **Risky change** (a drop, a narrowed column, a data move): a backup of the table before PROD, by the way in `_context/platform.md` §5.
- **First promotion to a new environment**: the per-environment values, identities and connections it needs exist there first. Without them the items deploy but do not run.

## The deployment note (in the PR description)

- Migrations: the numbers and files to apply, and what each does.
- ETL items, BI models and reports the change touches (exact names).
- Seed and grants to run after the migrations.
- Per-environment values that must exist in the target **before** the deploy (a new connection, a new variable).
- Manual steps the mechanism does not cover, in order.
- Loads to run in the target, and the check files to run after them.
- Risks, and the backup for each.
- The test document, linked.

## The test document: every deploy

Every change that is deployed gets one document: `qa/deploy/<branch topic>.md`, in the same PR (template: `qa/deploy/_template.md`). Ready-to-run queries and what each must return, so whoever deploys checks the result without thinking up the checks.

| Section | What it checks |
|---|---|
| 1. Structure | the migration log has the PR's migrations, executed, no error; every new or changed object exists, columns and types as its file |
| 2. Load | each load run twice: the same counts (idempotent); staging and gold counts |
| 3. Data | the `qa/data/<TABLE>.sql` checks of every changed table: all `PASS` |
| 4. ETL items | which item to run, the expected status of the item and of its steps; quality gates pass |
| 5. Nothing else broke | counts of the tables the change touches but does not own, before and after |

- Per query: what it checks, the SQL in a code block, the **expected result**, and an empty column per environment (`DEV`, `TEST`, `PROD`) for the actual result.
- **Expected = a rule that holds on any data** (`= 0`, `= COUNT(DISTINCT …) + 1`, `= the row count of run 1`). A fixed number only when it is DEV test data, and marked so. TEST has other data; a fixed number there is a false alarm.
- Counts, sums and statuses only. No query returns rows of people or customers.
- **What was not tested is written as a check marked `not run`, with the reason** (no connection, test data loaded by SQL instead of the ETL item…). A silent gap reads as a pass.
- **DEV column:** filled before the PR, by the AI or from a person's pasted results (`run by:` says which). Anything not as expected: fixed before the PR, or written in the PR as a known issue.
- **TEST and PROD columns:** filled by whoever deployed there, then committed. In PROD at least sections 1 and 3.
- The filled document stays in the repo: the record of what was checked where.

## Pre-checks (in DEV, before the PR)

- [ ] every database change has its object file **and** its migration, and they agree
- [ ] DEV is at the last migration: nothing pending in the log
- [ ] the repo and DEV agree (`nogamy-dev-workflow` step 5)
- [ ] no ETL item carries a server, ID, path or environment name (search the definitions for them)
- [ ] every check in `qa/data/` for the changed tables passes, twice
- [ ] test document written, `DEV` column filled and as expected
- [ ] try-out leftovers in DEV listed under "DEV cleanup before merge"

## After the deploy (the person)

1. PROD: before the click, compare the deployment note with what TEST received.
2. Check that the deploy itself ended in success, step by step.
3. Compare the migration log in the target with the deployment note.
4. Seed, grants and manual steps, if the mechanism does not run them.
5. Run the loads, then the test document: fill the column of this environment, commit it.
6. Something is not as expected → stop before the next environment. `nogamy-troubleshoot`.

## Platform specifics

> Skills are core and read-only in a project. Platform facts come from, in order:
> 1. `references/<platform>.md` in this folder, for each platform named in `_context/platform.md` §2 (shipped: `fabric.md`, `sqlserver.md`, `adf.md`, `airflow.md`).
> 2. `_context/platform.md` §10 → `nogamy-deploy`: what this project adds or overrides.
> 3. Neither exists → the table below is the question list: fill the answers in `_context/platform.md` §10 at setup (`nogamy-project-setup`), verified in the official docs (`nogamy-platform-watch`).

One column per hop.

| Topic | DEV → TEST | TEST → PROD |
|---|---|---|
| Mechanism (manual / platform tool / CI/CD) | ? | ? |
| Trigger, and who | ? | ? |
| How migrations are applied | ? | ? |
| How ETL items move | ? | ? |
| How the BI model and reports move | ? | ? |
| Per-environment values: where, and who sets them | ? | ? |
| What the mechanism does not move | ? | ? |
| Backup before a risky change; rollback | ? | ? |
| Release window, outside approvals | ? | ? |

Known traps of this platform's deployment (verified, `nogamy-platform-watch`): ?
