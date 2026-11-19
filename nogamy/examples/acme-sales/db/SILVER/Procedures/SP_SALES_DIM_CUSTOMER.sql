--------------------------------------------------------
-- SILVER.SP_SALES_DIM_CUSTOMER
-- Loads GOLD.SALES_DIM_CUSTOMER: view -> silver staging -> gold. Full reload. Idempotent.
-- Reads SILVER.V_SALES_DIM_CUSTOMER_FINAL_STEP (all business logic is in the views; none here).
-- Returns one row: SILVER_ROWS, GOLD_ROWS. On any error: rolls back and re-raises the error.
--------------------------------------------------------
CREATE PROCEDURE SILVER.SP_SALES_DIM_CUSTOMER
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
