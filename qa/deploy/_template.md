# Test document: <what was deployed>

Branch `<branch>` · migrations `<NNNN>`, `<NNNN>` · seed `<file>` · ETL items `<names>`.
Run after the deploy, in order. Fill the column of the environment you deployed to.
Expected results are rules that hold on any data. Counts, sums and statuses only.

## 1. Structure

**1.1 Migrations ran, without error**

```sql
SELECT RUN_ORDER, IS_EXECUTED, ERROR_MSG FROM MNG.MNG_MIGRATION_LOG WHERE RUN_ORDER IN (<numbers>);
```

| Expected | DEV | TEST | PROD |
|---|---|---|---|
| one row per migration, `IS_EXECUTED = 1`, `ERROR_MSG` empty | | | |

**1.2 Every new or changed object exists, columns and types as its file**

| Expected | DEV | TEST | PROD |
|---|---|---|---|
| | | | |

## 2. Load

**2.1 Each load run twice: the same counts**

| Expected | DEV | TEST | PROD |
|---|---|---|---|
| run 2 = run 1 | | | |

## 3. Data

**3.1 `qa/data/<TABLE>.sql` for every changed table**

| Expected | DEV | TEST | PROD |
|---|---|---|---|
| every check `PASS` | | | |

## 4. ETL items

**4.1 `<item>` run with `<parameters>`**

| Expected | DEV | TEST | PROD |
|---|---|---|---|
| ends in success; every step inside it succeeded, not only the item | | | |

## 5. Nothing else broke

Counts of the tables this change touches but does not own, before and after.

| Expected | DEV | TEST | PROD |
|---|---|---|---|
| unchanged | | | |

## Not run

Every check that was not run, with the reason. A silent gap reads as a pass.

- <check>: not run — <reason>
