--------------------------------------------------------
-- SILVER.V_SALES_DIM_CUSTOMER_FINAL_STEP
-- Step 2 of 2 for GOLD.SALES_DIM_CUSTOMER (full reload): one row per customer (rank 1, BR-001),
-- the STT transformations (BR-002, BR-003, BR-004), and the '-99' row (UNION ALL).
-- Final column list, exactly as the gold table without the ETL columns.
-- STEP2_KEYS, STEP3_NA and STEP4_ETL are skipped: no key lookups, and the few transformations read well here.
--------------------------------------------------------
CREATE VIEW SILVER.V_SALES_DIM_CUSTOMER_FINAL_STEP
AS
SELECT
    S.CUSTOMER_ID                                         AS KEY_CUSTOMER,
    TRIM(S.CUSTOMER_NAME)                                 AS CUSTOMER_NAME,
    S.BRANCH_CODE                                         AS BRANCH_CODE,
    COALESCE(NULLIF(TRIM(S.CITY_NAME), N''), N'לא ידוע')  AS CITY_NAME,
    CASE S.SEGMENT_CODE
        WHEN 'RT' THEN N'קמעונאות'
        WHEN 'WH' THEN N'סיטונאות'
        ELSE N'לא ידוע'
    END                                                   AS SEGMENT_NAME,
    CAST(CASE WHEN S.STATUS_CODE = 'A' THEN 1 ELSE 0 END AS BIT) AS IS_ACTIVE_IND,
    S.CREATED_DATE                                        AS CUSTOMER_CREATED_DATE
FROM SILVER.V_SALES_DIM_CUSTOMER_STEP1_SOURCE AS S
WHERE S.CUSTOMER_ROW_RANK = 1

UNION ALL

SELECT
    '-99'                AS KEY_CUSTOMER,
    N'לא ידוע'           AS CUSTOMER_NAME,
    '-99'                AS BRANCH_CODE,
    N'לא ידוע'           AS CITY_NAME,
    N'לא ידוע'           AS SEGMENT_NAME,
    CAST(0 AS BIT)       AS IS_ACTIVE_IND,
    CAST(NULL AS DATE)   AS CUSTOMER_CREATED_DATE;
