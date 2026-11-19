# Oracle as a source

Part of `nogamy-bronze-load`. Open before writing a `SOURCE_QUERY` or a bronze table for an Oracle source. What the platform's copy step adds or breaks: the platform reference (on Fabric: `fabric-oracle-gateway.md`).

## Types

- Read the real types from Oracle's catalog (`ALL_TAB_COLUMNS`: structure only, no values). Do not trust the type a column name suggests: a `LAST_UPDATE_DATE` in a view can be `CHAR(1)`.
- `VARCHAR2(n)` / `CHAR(n)`: `n` usually counts **bytes**. Hebrew takes 2 bytes per letter in UTF-8: size the bronze column by bytes, not letters.
- `CHAR(n)` is padded with spaces; compare and key on it knowing that.
- `DATE` carries a time part (to the second).
- `NUMBER(p,0)`: an integer; size it by `p` (up to 9 → 32-bit, 10–18 → 64-bit).
- `NUMBER` without precision (and the result of `COUNT(*)`): no fixed type. Cast it in the query: `TO_CHAR(col)` into a text bronze column, or `CAST(col AS NUMBER(p,s))` matching the bronze column.
- The mapping per project (Oracle type → bronze type → what the query must cast) goes in `sources/<system>/README.md`.

## ETL columns in the source query

Fill the ETL columns in the Oracle query itself, in UTC, wrapping the config query. The config query lists the source columns only:

```sql
SELECT q.*,
       SYS_EXTRACT_UTC(SYSTIMESTAMP) AS LOAD_TO_BRONZE_TS,
       CAST(1 AS NUMBER(9))          AS IS_LAST_INSERT_TO_BRONZE_IND,
       SYS_EXTRACT_UTC(SYSTIMESTAMP) AS ETL_INSERT_DATE,
       SYS_EXTRACT_UTC(SYSTIMESTAMP) AS ETL_UPDATE_DATE
FROM (<SOURCE_QUERY>) q
```

## Checking a new table

Before writing the `SOURCE_QUERY` for a new table, land it once into a `BRONZE.TRY_` table and read the types that arrived; drop the table after (`nogamy-db-objects` → try-outs).

## Delta window

`WHERE <change column> >= TO_DATE('<from>', 'YYYY-MM-DD HH24:MI:SS')`. A `DELTA` load on Oracle only after the proof in `merge-load.md`.
