---
name: nogamy-dev-workflow
description: The end-to-end routine for a development task at any access level — plan, branch, build files, run in DEV (by the AI, or by a person from a run sheet), self-check twice, commit, compare repo with DEV, hand over. Use for any task that changes tables, views, procedures or ETL items.
---

# Development task, end to end

The AI works **only in DEV**, as the AI identity (`PROJECT.md` → Environments), at the access level in `_context/platform.md` §7. TEST and PROD are reached by promotion (`nogamy-deploy`), never by the AI.

**Whatever the level allows, the AI runs itself.** It does not hand a person a step it can run. The person keeps: plan approval (step 1), review, push and merge (step 6), and everything under "Never". A person runs a loop step only when they ask to.

## 1. Plan (stop for approval)

- Follow the read order in `AGENTS.md`; then the STT of the entity and what exists in DEV (structure only).
- Present, in the format of `nogamy-plan-and-explain`: objects to create or change (with file paths), the load pattern, the checks that will prove it is right, **who runs what**.
- Wait for "approved". An architecture choice still open → stop and name its owner.

## 2. Branch and files

- A topic branch (`nogamy-git-workflow`). Never work on the main branch.
- Database objects: one file each (`nogamy-db-objects`), **plus** the next numbered migration in `scripts/migrations/` (`scripts/README.md`).
- ETL items: one folder per project and layer (`nogamy-build-pipeline`).
- Checks: `qa/data/<GOLD TABLE>.sql` (`nogamy-qa-checks`).
- Test document: `qa/deploy/<branch topic>.md` (`nogamy-deploy`).
- Folder layout of this platform: "Platform specifics".

## 3. Run in DEV

Who presses Run depends on the level. What is run does not.

| Step | L0 / L1 | L2 | L3 |
|---|---|---|---|
| apply the migration | run sheet → person | AI | AI |
| run the load procedure | run sheet → person | AI | AI |
| run the checks | L0: run sheet · L1: AI (read-only) | AI | AI |
| publish and run the ETL item | run sheet → person | run sheet → person | AI |

- DEV gets a change the same way TEST and PROD will: through the migration, never by running the object file directly.
- A migration with a drop or a delete is run by the developer, at every level.
- A try-out before the migration is final: temp tables and ad-hoc queries only (`nogamy-db-objects`).

### The run sheet

What the AI hands a person when it cannot run something itself. One block, in order:

```
## Run sheet — <task> — DEV
1. <what this step does>
   Run: <the exact command, or the file to run>
   Expect: <the result that means it worked: a count, a status, "no rows">
   Paste back: <exactly what to copy: the result table / the error text>
2. …
Stop at the first step that does not match "Expect", and paste what you got.
```

- Every step has an expected result. A step without one is not checkable.
- Ask only for counts, statuses and error texts. Never for rows.
- Wait for the pasted results. **Never continue as if a step passed.**
- The pasted results go into the test document, marked `run by: <person>`.

## 4. Check yourself

- Every check returns `PASS` / `FAIL`. Run the load **twice**: the second run must give the same result (idempotency).
- On `FAIL`: read the error, fix the file, apply, run again. **Max 3 attempts**, then stop and report what failed and why (`nogamy-troubleshoot`).
- A clean comparison of definitions does not prove it works. Run it.
- Never print rows of people or customers. Counts, sums, structure only.

## 5. Commit and compare with DEV

- Commit when asked: small, `<scope>: <what> — <why>` (`nogamy-git-workflow`).
- Compare the repo with DEV (the drift check in `PROJECT.md` → Agent tools): every object in the repo exists in DEV as written, and every object in DEV has a file.
- A difference → fix before the PR. Objects in DEV without a file: add the file, or list them for the developer to drop.

## 6. Hand over

Tell the developer: what changed, the files, the check results of both runs and who ran them, the comparison with DEV, what was **not** run and why. The developer reviews, pushes and opens the PR (`nogamy-git-workflow`). The AI does not push and does not merge.

## Never

- Touch TEST, PROD or any BI environment. Never add them to an allow list.
- Delete objects or data. A drop is done by the developer and recorded in the PR.
- Change permissions.
- Leave work tables in DEV: use temp tables. Anything left over: list it for the developer to drop.
- Report a result nobody ran.

## Platform specifics

> Skills are core and read-only in a project. Platform facts come from, in order:
> 1. `references/<platform>.md` in this folder, for each platform named in `_context/platform.md` §2 (shipped: `fabric.md`, `sqlserver.md`, `adf.md`, `airflow.md`).
> 2. `_context/platform.md` §10 → `nogamy-dev-workflow`: what this project adds or overrides.
> 3. Neither exists → the table below is the question list: fill the answers in `_context/platform.md` §10 at setup (`nogamy-project-setup`), verified in the official docs (`nogamy-platform-watch`).

| Topic | This project |
|---|---|
| Access level | ? |
| Folder layout of database objects and ETL items | ? |
| Run a query / a `.sql` file in DEV | ? (the exact command) |
| Apply migrations in DEV | ? |
| Publish an ETL item to DEV | ? |
| Run an ETL item and read the status of its steps | ? |
| Compare repo with DEV | ? |
| What a person must do by hand in the tool's UI (create an empty item, share a connection…) | ? |
