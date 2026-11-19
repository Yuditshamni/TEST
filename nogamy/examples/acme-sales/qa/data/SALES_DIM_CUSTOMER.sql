--------------------------------------------------------
-- qa/data/SALES_DIM_CUSTOMER.sql
-- Per-table checks for GOLD.SALES_DIM_CUSTOMER (full reload). One row per check: CHECK_NAME, ACTUAL, EXPECTED, RESULT.
-- Every check is a rule that holds on any data; no fixed numbers. Counts only, no customer rows.
-- Run: after SILVER.SP_SALES_DIM_CUSTOMER; then run the load again and these checks again: same result = idempotent.
--------------------------------------------------------
SELECT
    'rows > 0'                                  AS CHECK_NAME,
    CAST(COUNT(*) AS VARCHAR(20))               AS ACTUAL,
    '>0'                                        AS EXPECTED,
    CASE WHEN COUNT(*) > 0 THEN 'PASS' ELSE 'FAIL' END AS RESULT
FROM GOLD.SALES_DIM_CUSTOMER

UNION ALL

SELECT
    'grain: one row per KEY_CUSTOMER (duplicate keys)',
    CAST(COUNT(*) AS VARCHAR(20)),
    '0',
    CASE WHEN COUNT(*) = 0 THEN 'PASS' ELSE 'FAIL' END
FROM (SELECT KEY_CUSTOMER
      FROM GOLD.SALES_DIM_CUSTOMER
      GROUP BY KEY_CUSTOMER
      HAVING COUNT(*) > 1) AS D

UNION ALL

SELECT
    'no NULL KEY_CUSTOMER',
    CAST(COUNT(*) AS VARCHAR(20)),
    '0',
    CASE WHEN COUNT(*) = 0 THEN 'PASS' ELSE 'FAIL' END
FROM GOLD.SALES_DIM_CUSTOMER
WHERE KEY_CUSTOMER IS NULL

UNION ALL

SELECT
    'exactly one -99 row',
    CAST(COUNT(*) AS VARCHAR(20)),
    '1',
    CASE WHEN COUNT(*) = 1 THEN 'PASS' ELSE 'FAIL' END
FROM GOLD.SALES_DIM_CUSTOMER
WHERE KEY_CUSTOMER = '-99'

UNION ALL

SELECT
    'gold rows = distinct bronze keys + 1',
    CAST(G.GOLD_ROWS AS VARCHAR(20)),
    CAST(B.BRONZE_KEYS + 1 AS VARCHAR(20)),
    CASE WHEN G.GOLD_ROWS = B.BRONZE_KEYS + 1 THEN 'PASS' ELSE 'FAIL' END
FROM (SELECT COUNT(*) AS GOLD_ROWS
      FROM GOLD.SALES_DIM_CUSTOMER) AS G
CROSS JOIN (SELECT COUNT(DISTINCT CUSTOMER_ID) AS BRONZE_KEYS
            FROM BRONZE.BRONZE_ERP_CUSTOMERS
            WHERE IS_LAST_INSERT_TO_BRONZE_IND = 1) AS B

UNION ALL

SELECT
    'IS_LAST_UPDATE_IND = 1 on every row (full reload)',
    CAST(COUNT(*) AS VARCHAR(20)),
    '0',
    CASE WHEN COUNT(*) = 0 THEN 'PASS' ELSE 'FAIL' END
FROM GOLD.SALES_DIM_CUSTOMER
WHERE IS_LAST_UPDATE_IND IS NULL OR IS_LAST_UPDATE_IND <> 1

UNION ALL

SELECT
    'SEGMENT_NAME: accepted values only',
    CAST(COUNT(*) AS VARCHAR(20)),
    '0',
    CASE WHEN COUNT(*) = 0 THEN 'PASS' ELSE 'FAIL' END
FROM GOLD.SALES_DIM_CUSTOMER
WHERE SEGMENT_NAME NOT IN (N'קמעונאות', N'סיטונאות', N'לא ידוע');
