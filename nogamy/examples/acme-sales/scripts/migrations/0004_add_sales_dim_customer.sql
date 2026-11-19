-- migration: 0004
-- PR: example
-- Creates GOLD.SALES_DIM_CUSTOMER with its silver staging table, its two silver views and its full-reload load procedure.

--------------------------------------------------------
-- GOLD.SALES_DIM_CUSTOMER
-- Customer dimension. Grain: one row per customer (KEY_CUSTOMER), plus the '-99' row. Full reload.
-- Spec: stt/sales/SALES_DIM_CUSTOMER.md. Loaded by SILVER.SP_SALES_DIM_CUSTOMER.
-- No PK (project policy: none); uniqueness is proven by qa/data/SALES_DIM_CUSTOMER.sql.
--------------------------------------------------------
IF OBJECT_ID(N'GOLD.SALES_DIM_CUSTOMER', N'U') IS NULL
CREATE TABLE GOLD.SALES_DIM_CUSTOMER
(
    KEY_CUSTOMER           VARCHAR(10)   NOT NULL,
    CUSTOMER_NAME          NVARCHAR(100) NULL,
    BRANCH_CODE            VARCHAR(5)    NULL,
    CITY_NAME              NVARCHAR(50)  NOT NULL,
    SEGMENT_NAME           NVARCHAR(30)  NOT NULL,
    IS_ACTIVE_IND          BIT           NOT NULL,
    CUSTOMER_CREATED_DATE  DATE          NULL,
    IS_LAST_UPDATE_IND     BIT           NOT NULL,
    ETL_INSERT_DATE        DATETIME2(6)  NOT NULL,
    ETL_UPDATE_DATE        DATETIME2(6)  NOT NULL
);
GO
--------------------------------------------------------
-- SILVER.SILVER_SALES_DIM_CUSTOMER
-- Silver staging of GOLD.SALES_DIM_CUSTOMER: freezes one load. The gold columns without ETL_UPDATE_DATE.
-- No LOAD_TO_BRONZE_TS: full reload, no watermark. Emptied and filled by SILVER.SP_SALES_DIM_CUSTOMER.
--------------------------------------------------------
IF OBJECT_ID(N'SILVER.SILVER_SALES_DIM_CUSTOMER', N'U') IS NULL
CREATE TABLE SILVER.SILVER_SALES_DIM_CUSTOMER
(
    KEY_CUSTOMER           VARCHAR(10)   NOT NULL,
    CUSTOMER_NAME          NVARCHAR(100) NULL,
    BRANCH_CODE            VARCHAR(5)    NULL,
    CITY_NAME              NVARCHAR(50)  NOT NULL,
    SEGMENT_NAME           NVARCHAR(30)  NOT NULL,
    IS_ACTIVE_IND          BIT           NOT NULL,
    CUSTOMER_CREATED_DATE  DATE          NULL,
    IS_LAST_UPDATE_IND     BIT           NOT NULL,
    ETL_INSERT_DATE        DATETIME2(6)  NOT NULL
);
GO
--------------------------------------------------------
-- SILVER.V_SALES_DIM_CUSTOMER_STEP1_SOURCE
-- Step 1 of 2 for GOLD.SALES_DIM_CUSTOMER (full reload): the source columns, the bronze filter,
-- and the rank of each row inside its customer (BR-001: latest UPDATED_AT first, then the higher BRANCH_CODE).
-- Why two views: keeping only rank 1 needs the rank computed first, so the filter sits in the next view.
-- Reads only its own bronze table.
--------------------------------------------------------
CREATE OR ALTER VIEW SILVER.V_SALES_DIM_CUSTOMER_STEP1_SOURCE
AS
SELECT
    B.CUSTOMER_ID,
    B.BRANCH_CODE,
    B.CUSTOMER_NAME,
    B.CITY_NAME,
    B.SEGMENT_CODE,
    B.STATUS_CODE,
    B.CREATED_DATE,
    B.UPDATED_AT,
    ROW_NUMBER() OVER (PARTITION BY B.CUSTOMER_ID
                       ORDER BY B.UPDATED_AT DESC, B.BRANCH_CODE DESC) AS CUSTOMER_ROW_RANK
FROM BRONZE.BRONZE_ERP_CUSTOMERS AS B
WHERE B.IS_LAST_INSERT_TO_BRONZE_IND = 1
  AND B.CUSTOMER_ID IS NOT NULL;
GO
--------------------------------------------------------
-- SILVER.V_SALES_DIM_CUSTOMER_FINAL_STEP
-- Step 2 of 2 for GOLD.SALES_DIM_CUSTOMER (full reload): one row per customer (rank 1, BR-001),
-- the STT transformations (BR-002, BR-003, BR-004), and the '-99' row (UNION ALL).
-- Final column list, exactly as the gold table without the ETL columns.
-- STEP2_KEYS, STEP3_NA and STEP4_ETL are skipped: no key lookups, and the few transformations read well here.
--------------------------------------------------------
CREATE OR ALTER VIEW SILVER.V_SALES_DIM_CUSTOMER_FINAL_STEP
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
GO
--------------------------------------------------------
-- SILVER.SP_SALES_DIM_CUSTOMER
-- Loads GOLD.SALES_DIM_CUSTOMER: view -> silver staging -> gold. Full reload. Idempotent.
-- Reads SILVER.V_SALES_DIM_CUSTOMER_FINAL_STEP (all business logic is in the views; none here).
-- Returns one row: SILVER_ROWS, GOLD_ROWS. On any error: rolls back and re-raises the error.
--------------------------------------------------------
CREATE OR ALTER PROCEDURE SILVER.SP_SALES_DIM_CUSTOMER
AS
BEGIN
    SET NOCOUNT ON;
    SET XACT_ABORT ON;
    DECLARE @NOW DATETIME2(6) = CAST(SYSUTCDATETIME() AS DATETIME2(6));

    BEGIN TRY
        BEGIN TRANSACTION;

        -- 1. silver staging: freeze this load
        TRUNCATE TABLE SILVER.SILVER_SALES_DIM_CUSTOMER;
        INSERT INTO SILVER.SILVER_SALES_DIM_CUSTOMER
        (
            KEY_CUSTOMER,
            CUSTOMER_NAME,
            BRANCH_CODE,
            CITY_NAME,
            SEGMENT_NAME,
            IS_ACTIVE_IND,
            CUSTOMER_CREATED_DATE,
            IS_LAST_UPDATE_IND,
            ETL_INSERT_DATE
        )
        SELECT
            KEY_CUSTOMER,
            CUSTOMER_NAME,
            BRANCH_CODE,
            CITY_NAME,
            SEGMENT_NAME,
            IS_ACTIVE_IND,
            CUSTOMER_CREATED_DATE,
            1,
            @NOW
        FROM SILVER.V_SALES_DIM_CUSTOMER_FINAL_STEP;

        -- 2. gold: full reload from staging
        TRUNCATE TABLE GOLD.SALES_DIM_CUSTOMER;
        INSERT INTO GOLD.SALES_DIM_CUSTOMER
        (
            KEY_CUSTOMER,
            CUSTOMER_NAME,
            BRANCH_CODE,
            CITY_NAME,
            SEGMENT_NAME,
            IS_ACTIVE_IND,
            CUSTOMER_CREATED_DATE,
            IS_LAST_UPDATE_IND,
            ETL_INSERT_DATE,
            ETL_UPDATE_DATE
        )
        SELECT
            KEY_CUSTOMER,
            CUSTOMER_NAME,
            BRANCH_CODE,
            CITY_NAME,
            SEGMENT_NAME,
            IS_ACTIVE_IND,
            CUSTOMER_CREATED_DATE,
            IS_LAST_UPDATE_IND,
            ETL_INSERT_DATE,
            @NOW
        FROM SILVER.SILVER_SALES_DIM_CUSTOMER;

        COMMIT TRANSACTION;

        SELECT (SELECT COUNT(*) FROM SILVER.SILVER_SALES_DIM_CUSTOMER) AS SILVER_ROWS,
               (SELECT COUNT(*) FROM GOLD.SALES_DIM_CUSTOMER)          AS GOLD_ROWS;
    END TRY
    BEGIN CATCH
        IF @@TRANCOUNT > 0 ROLLBACK TRANSACTION;
        THROW;
    END CATCH
END;
GO
