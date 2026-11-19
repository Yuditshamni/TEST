---
name: nogamy-write-sql
description: Write correct, readable, fast SQL for this project's database — the dialect's differences, case sensitivity, common patterns (dedup, latest row, orphans, safe division), performance habits, and a debugging checklist. Use for any ad-hoc query, check, or view logic.
---

# SQL for this project's database

For objects saved in the repo (tables, views, procedures) also follow `nogamy-db-objects`. The dialect is named in `_context/platform.md` §2; its details are in "Platform specifics" below. **Until a source there answers a topic, write plain standard SQL and say which parts must be checked against the dialect.**

## Habits that hold in any dialect

- References as `SCHEMA.OBJECT` (two-part). Never a database or server name.
- Explicit `INNER JOIN` / `LEFT JOIN`. Alias every table; qualify every column in a join.
- Name the columns. No `SELECT *` in saved code.
- Compare codes on purpose: know whether names and data are case sensitive, and whether trailing spaces count. Match the exact case, or `UPPER()` both sides on purpose.
- Safe division: `x / NULLIF(y, 0)`.
- `NULL` is not `''` and not `'N/A'`: decide which one a column uses, and check.
- Dates: say the time zone. Load times in UTC; business dates in the client's time, converted explicitly.
- Cast explicitly. An implicit conversion is slow and hides bugs.

## Patterns

```sql
-- latest row per key
SELECT *
FROM (
    SELECT t.*,
           ROW_NUMBER() OVER (PARTITION BY CUSTOMER_ID ORDER BY LAST_UPDATE_DATE DESC) AS RN
    FROM BRONZE.BRONZE_CRM_CUSTOMERS AS t
) AS x
WHERE RN = 1;

-- duplicates of a key
SELECT KEY_CUSTOMER, COUNT(*) AS CNT
FROM GOLD.SALES_DIM_CUSTOMER
GROUP BY KEY_CUSTOMER
HAVING COUNT(*) > 1;

-- orphan fact keys
SELECT f.KEY_CUSTOMER, COUNT(*) AS CNT
FROM GOLD.SALES_FACT_ORDERS AS f
LEFT JOIN GOLD.SALES_DIM_CUSTOMER AS d ON d.KEY_CUSTOMER = f.KEY_CUSTOMER
WHERE d.KEY_CUSTOMER IS NULL
GROUP BY f.KEY_CUSTOMER;

-- row count before and after a join: a jump means a fan-out
SELECT (SELECT COUNT(*) FROM <left side>) AS BEFORE_JOIN, COUNT(*) AS AFTER_JOIN FROM <the join>;
```

CTEs are fine in queries and checks. Silver logic lives in views: a CTE pyramid or a heavy subquery is the sign to split into another view (`nogamy-db-objects`).

## Performance

- Select only the columns you need.
- Filter early, on the column the platform prunes by (usually a date).
- A heavy intermediate result → a temp table, never a permanent work table.
- Join on columns of the same type.
- Check the row count after every join.
- Measure before optimizing: a claim that something is slow comes with a number.

## Reading data safely

Queries that return rows of people or customers are never run by the AI and never requested in a run sheet (`nogamy-explore-data`). Counts, sums, lengths, structure.

## Debugging

1. Object not found → schema, exact spelling and case, two-part name, no database name.
2. Type mismatch → cast explicitly; read the real type from the catalog.
3. Wrong numbers → count rows per join step; look for many-to-many.
4. Divide by zero → `NULLIF`.
5. Ambiguous column → alias every column in joins.
6. Still unclear → search the official docs for the exact error text before guessing (`nogamy-platform-watch`).

## Platform specifics

Skills are core and read-only in a project. Platform facts come from, in order:
1. `references/<platform>.md` in this folder, for each platform named in `_context/platform.md` §2 (shipped: `fabric.md`, `sqlserver.md`).
2. `_context/platform.md` §10 → `nogamy-write-sql`: what this project adds or overrides.
3. Neither exists → the table below is the question list: fill the answers in `_context/platform.md` §10 at setup (`nogamy-project-setup`), verified in the official docs (`nogamy-platform-watch`).

| Topic | This project |
|---|---|
| Dialect and version | ? |
| Case sensitivity: names · data · `LIKE` | ? |
| Types to use · types that do not exist | ? |
| Row limiting (`TOP` / `LIMIT` / `FETCH FIRST`) | ? |
| String functions that differ (`LEN` / `LENGTH`, concatenation, aggregation) | ? |
| Date functions and time-zone conversion | ? |
| NULL-safe comparison (`IS NOT DISTINCT FROM` or its equivalent) | ? |
| `MERGE`, transactions, error handling: supported? limits? | ? |
| Temp tables: syntax and scope | ? |
| Constraints and indexes: enforced? available? | ? |
| The system catalog: where columns and objects are listed | ? |
| Known traps | ? |
