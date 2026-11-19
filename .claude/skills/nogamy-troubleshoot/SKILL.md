---
name: nogamy-troubleshoot
description: Diagnose a failure — an ETL run failed, a procedure error, wrong numbers after a load, a refused deployment, a login or permission error — with a fixed order of checks and a growing table of known causes. Use when something fails in DEV or a developer reports an error.
---

# Troubleshoot

Order: read the error → reproduce in DEV → find the cause → **plan the fix** (`nogamy-plan-and-explain`) → fix in the repo → apply → run again. **Max 3 fix attempts**, then stop and report what was tried and what you suspect.

## 1. Get the facts

- ETL item: its status, its failure reason, **and the status of every step inside it**. An item can end in success while a step failed.
- Procedure: run it alone, with the same parameters.
- Wrong numbers: `nogamy-reconcile-numbers` at total → month → one dimension.
- Copy the exact error text. Search it in the official docs before guessing (`nogamy-platform-watch`).
- At L0 or L1 (`AGENTS.md`): ask the person for the exact error text and the result of one named query at a time. Never ask for "the logs".

A diagnosis is read-only. Nothing changes until the fix is planned and approved.

## 2. Known causes

Generic rows ship with the core; platform rows are in `references/<platform>.md`. A cause met only in this project goes to `_context/platform.md` §10 → `nogamy-troubleshoot`.

| Symptom | Usual cause | Fix |
|---|---|---|
| object not found | wrong schema, wrong case, a database name inside the code | exact name and case, `SCHEMA.OBJECT` |
| an item in TEST reads DEV data | a server, ID or path typed into the item | the per-environment mechanism (`_context/platform.md` §5) |
| a load ran twice → duplicates | not idempotent | merge / delete-by-key (`nogamy-db-objects`) |
| watermark did not move | updated outside the transaction, or a failure before it | inside the transaction, after the load |
| watermark moved, data missing | advanced before the quality gate | advance only after the gate passes |
| gold emptied after a failed load | a truncate before a copy that failed, and gold reloaded in full | gate on empty bronze; land in staging first (`nogamy-bronze-load`) |
| an environment differs from DEV | a migration did not run there | compare `MNG.MNG_MIGRATION_LOG` across environments; a dry run of the migrations shows what is pending |
| a migration failed half way | a statement without a guard | add the guard (`scripts/README.md`), re-run: the file runs again from the top |
| permission error for the AI's identity | not granted in DEV, or reaching outside DEV | grant in DEV only; outside DEV is intended |
| the tools refuse a target (allow list) | the guard that keeps the AI in DEV | intended; never add TEST or PROD |
| login refused for a service identity | the secret's ID stored instead of its value, or the secret expired | a new secret; store the value |
| the BI model shows DEV data after a deploy | the model was not re-pointed to the target | the per-environment rule of the BI tool (`nogamy-deploy`) |
| numbers differ from the legacy by a few rows | `-99` rows, an excluded population, a month boundary in UTC, case in codes | `nogamy-reconcile-numbers` pitfalls |
| type error while loading from a source | the type was guessed from the column's name | read the real type from the source catalog (`nogamy-bronze-load`) |

## 3. Report

```
What failed: …
Cause: … (with the evidence: error text, query result)
Fix: … (files changed)
Result after fix: … (run status, checks) — run by: <AI / person>
```

New cause found → a row in `_context/platform.md` §10 → `nogamy-troubleshoot`, in the same PR. A cause every project would meet → also `nogamy-feedback`, so the core gets the row. That table is the memory of what broke.

How to read a run's status and run a procedure on this platform: `references/<platform>.md` in this folder (shipped: `fabric.md`, `sqlserver.md`, `adf.md`, `airflow.md`), or `_context/platform.md` §10.
