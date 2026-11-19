---
name: nogamy-explore-data
description: Profile a source or warehouse table safely — structure, row count, null rates, cardinality, suspicious values, candidate keys — without ever reading sensitive values. Use when meeting a new source table, before writing an STT, when choosing a key or a load pattern, or when a table "looks wrong".
---

# Explore a table (no sensitive values)

The agent `nogamy-source-profiler` runs this skill and returns only the summary. How queries are run on the project's platform: `references/<platform>.md` (shipped: `fabric.md`, `sqlserver.md`).

## Rules first

- Read the column list and the `pii` flags first (`sources/<system>/<table>.md` or the STT). Unknown → treat as sensitive.
- For sensitive columns: only `COUNT`, `COUNT(DISTINCT)`, null count, min / max **length**. Never values, never the first rows of the table.
- DEV only. Who runs the queries follows the access level (`_context/platform.md` §7): the AI at L1 and above, as its own identity; at L0 the AI writes the queries, a person runs them and pastes the result table.
- A source system is profiled through the query the developer runs there, or through its copy in bronze.
- Dialect: `nogamy-write-sql`. The queries below are plain SQL; adjust function names (`LEN` / `LENGTH`) to the project's dialect.

## 1. Structure

From the catalog of the database (`INFORMATION_SCHEMA.COLUMNS` or its equivalent): column, type, length, nullable. Never guess a type from a column's name.

## 2. Profile, per column

```sql
SELECT 'CUSTOMER_STATUS'                                        AS column_name,
       COUNT(*)                                                 AS rows_total,
       SUM(CASE WHEN CUSTOMER_STATUS IS NULL THEN 1 ELSE 0 END) AS nulls,
       COUNT(DISTINCT CUSTOMER_STATUS)                          AS distinct_values,
       MIN(LENGTH(CUSTOMER_STATUS))                             AS min_len,
       MAX(LENGTH(CUSTOMER_STATUS))                             AS max_len
FROM BRONZE.BRONZE_CRM_CUSTOMERS;
```

Non-sensitive coded columns may add the value list: `SELECT CUSTOMER_STATUS, COUNT(*) … GROUP BY CUSTOMER_STATUS`.

## 3. Candidate key

```sql
SELECT COUNT(*) AS rows_total,
       COUNT(DISTINCT CUSTOMER_ID) AS distinct_keys,
       SUM(CASE WHEN CUSTOMER_ID IS NULL THEN 1 ELSE 0 END) AS null_keys
FROM BRONZE.BRONZE_CRM_CUSTOMERS;
```

- `rows_total = distinct_keys` and `null_keys = 0` → the key holds **on this data**. The business confirms that it holds by definition.
- Not unique → count the fully identical rows too. Identical rows mean no key can pass: an open question for the source owner, with the counts.
- A column that changes over time inside a key (an end date, an update date, a description) is a trap: every change looks like a delete plus a new row.

## What to flag

| Signal | Threshold |
|---|---|
| nulls | > 5% warn, > 20% alert |
| a key with duplicates | any |
| an "id" with very few distinct values | suspicious |
| a category with very many distinct values | suspicious |
| placeholders: `N/A`, `TBD`, `test`, `999999`, `1900-01-01` | any |
| future dates in history, negative amounts | any |
| trailing spaces, mixed case in codes | any (worse where the platform is case sensitive) |
| a change column that does not move on every change | any (it cannot drive a delta load) |

## Output

```
## Profile: <schema.table>   rows: <n>   date: <today>   run by: <AI / person>
| column | type | null % | distinct | note |
Issues: one line each, with the number
Candidate keys: …
Candidate joins: <column> → <table.column>
Questions for the analyst: …
```

For a source table, write the technical columns into `sources/<system>/<table>.md` (`nogamy-specs`); `meaning_he` stays for the analyst. Questions go to `_context/open-questions.md` with the counts, written so they can be sent to the client as is.
