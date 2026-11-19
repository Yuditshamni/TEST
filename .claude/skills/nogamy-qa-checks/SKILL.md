---
name: nogamy-qa-checks
description: Write and run data checks — per-table PASS/FAIL checks in qa/data/, the project end-to-end QA script, the quality framework that gates the loads, and golden questions. Use after building or changing a table, before a PR, and before a release.
---

# Quality checks

Who runs a check follows the access level (`_context/platform.md` §7). At L0 the checks go to a person in a run sheet (`nogamy-dev-workflow`) and the AI reads the pasted results. The checks themselves are the same. How to run them on the project's platform: `references/<platform>.md` (shipped: `fabric.md`, `sqlserver.md`).

## 1. Per-table checks: `qa/data/<GOLD TABLE>.sql`

One query returning one row per check:

```sql
SELECT 'rows' AS check_name, CAST(COUNT(*) AS VARCHAR(20)) AS actual, '>0' AS expected,
       CASE WHEN COUNT(*) > 0 THEN 'PASS' ELSE 'FAIL' END AS result
FROM GOLD.SALES_DIM_CUSTOMER
UNION ALL
SELECT 'duplicate keys', CAST(COUNT(*) AS VARCHAR(20)), '0',
       CASE WHEN COUNT(*) = 0 THEN 'PASS' ELSE 'FAIL' END
FROM (SELECT KEY_CUSTOMER FROM GOLD.SALES_DIM_CUSTOMER GROUP BY KEY_CUSTOMER HAVING COUNT(*) > 1) d
UNION ALL
SELECT 'null keys', …
UNION ALL
SELECT '-99 row exists', …
UNION ALL
SELECT 'total vs source', …;
```

Minimum per table:

| Dimension | Fact |
|---|---|
| rows > 0 | rows > 0 |
| no duplicate business key | no duplicate `FACT_KEY` |
| no NULL key | every `KEY_<ENTITY>` exists in its dimension (or `-99`) |
| `-99` row exists | totals equal the source: counts exact, amounts `ABS(a - b) < 0.01` |
| coded columns: accepted values only | share of `-99` keys below an agreed threshold |

Run the checks, run the load again, run the checks again: the same result = idempotent.

## 2. End-to-end: `qa/data/QA_<PROJECT>_END_TO_END.sql`

One file for the project (base §6b, company standard). Built **in parallel** with the silver views, not after.

| Phase | Checks |
|---|---|
| 1 | gold vs bronze totals per month: full outer join on month, counts exact, amounts `ABS(a - b) < 0.01` |
| 2 | bronze sanity: rows, dates in range, `IS_LAST` flags |
| 3 | silver vs bronze, and `-99` counts |
| 4 | gold integrity: duplicate `FACT_KEY`, sentinels, `IS_LAST_UPDATE_IND` (full reload: all `1`), NULL measures, orphan `KEY_<ENTITY>` |

- Every query returns a `RESULT` column: `OK` / `PROBLEM — <reason>` / `WARNING — <note>` / `NOTE — <context>`.
- Header at the top: project, purpose, how to run, phases.
- Add queries when: a new fact, column or dimension; a logic change; a new source; **every production bug**.
- Checks that prove useful move into the quality framework (section 3).
- Testing rules (base §9): duplicates, required NULLs, orphan keys, layer reconciliation, row counts per view step, and **re-run idempotency**.

## 3. The quality framework that gates the loads (base §4a, company recommendation)

Checks that run inside the pipelines, not by hand. Shared objects (names: `nogamy-naming`; a platform pack may ship them in a `QA` schema):

| Object | Holds |
|---|---|
| `MNG.MNG_DQA_QUERY` | `GROUP_NAME`, `DQA_TYPE` (`Duplicates` / `Empty_Table` / `Others`), `TABLE_NAME`, `TABLE_KEYS`, `DQA_QUERY`, `THRESHOLD`, `IS_ACTIVE` |
| `MNG.MNG_DQA_RESULT` | `RUN_TS`, `GROUP_NAME`, `DQA_TYPE`, `TABLE_NAME`, `TABLE_KEYS`, `RESULT_COUNT`, `THRESHOLD`, `PASS_IND`, `ERROR_MSG` — **never deleted** |
| `MNG.SP_DQA` | parameters `DQA_TYPE`, `TABLE_NAME`, `TABLE_KEYS`, `GROUP_NAME`, `THRESHOLD` (`NULL` = all); runs the matching active checks; fails the step when a check fails |

- Two ways to call: the registered checks, filtered by group, type or table; or an ad hoc gate after a bronze load (`DQA_TYPE` + `TABLE_NAME` + `TABLE_KEYS`, no config row needed).
- Fail when `RESULT_COUNT > THRESHOLD`.
- `Empty_Table` returns `COUNT(*) * -1`: threshold `-1` = fail if empty; `-100` = fail if fewer than 100 rows.
- An `Others` query returns rows **only** when there is a problem.
- Baseline for every gold table: duplicates on the key (threshold `0`) and empty table (threshold `-1`).
- Gates: after each bronze load; after the dimensions (`<Domain>_GOLD_Dims`); after the facts (`<Domain>_GOLD_Facts`). Facts wait for the dimensions gate.
- Quarantine of bad rows is not in the base: design it in the plan, ask before building.

## 4. Golden questions: `qa/golden/<domain>.md`

| question_he | expected_answer | proof_sql | status |
|---|---|---|---|

- Business questions with a known answer, in the users' words. Every question the client asks is a candidate.
- Before a release: answer each question from the new model (or ask the AI assistant that queries it), compare with `expected_answer`, report accuracy per domain.
- A wrong answer is fixed **in the model** (a description, a synonym, a missing measure), never in a prompt.

## 5. Test document per deploy: `qa/deploy/<branch topic>.md`

Every deploy is checked with a document the AI writes: queries to run and what each must return, one column per environment. Format and who fills what: `nogamy-deploy`. It reuses the checks above and adds structure, idempotency, ETL items and "nothing else broke".

## Rules

- Checks read counts and sums, never rows of people or customers.
- An expected result is a rule that holds on any data (`= 0`, `= the count of run 1`). A fixed number only for DEV test data, and marked so.
- A person still looks at 100 rows of every new table: automation catches only what it was told to catch.
- A check that was not run is written as `not run`, with the reason. A silent gap reads as a pass.
