# Load procedure templates — Microsoft Fabric

Part of `nogamy-db-objects`. Read when `_context/platform.md` §2 names Fabric. The same frame as `load-procedure-templates.md`, in Fabric Warehouse T-SQL.

## Full reload (example: `SILVER.SP_SALES_DIM_CUSTOMER`)

```sql
--------------------------------------------------------
-- SILVER.SP_SALES_DIM_CUSTOMER
-- Loads GOLD.SALES_DIM_CUSTOMER: view -> silver staging -> gold. Full reload. Idempotent.
--------------------------------------------------------
CREATE PROCEDURE SILVER.SP_SALES_DIM_CUSTOMER
AS
BEGIN
    SET NOCOUNT ON;
    DECLARE @NOW DATETIME2(6) = CAST(SYSUTCDATETIME() AS DATETIME2(6));

    BEGIN TRY
        BEGIN TRANSACTION;

        -- 1. silver staging: freeze this load
        TRUNCATE TABLE SILVER.SILVER_SALES_DIM_CUSTOMER;
        INSERT INTO SILVER.SILVER_SALES_DIM_CUSTOMER (KEY_CUSTOMER, ..., IS_LAST_UPDATE_IND, ETL_INSERT_DATE)
        SELECT KEY_CUSTOMER, ..., 1, @NOW
        FROM SILVER.V_SALES_DIM_CUSTOMER;

        -- 2. gold: full reload from staging
        TRUNCATE TABLE GOLD.SALES_DIM_CUSTOMER;
        INSERT INTO GOLD.SALES_DIM_CUSTOMER (KEY_CUSTOMER, ..., IS_LAST_UPDATE_IND, ETL_INSERT_DATE, ETL_UPDATE_DATE)
        SELECT KEY_CUSTOMER, ..., IS_LAST_UPDATE_IND, ETL_INSERT_DATE, @NOW
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
```

## Delta, match by key

Same frame; step 2 and the watermark as in `load-procedure-templates.md`, with `@NOW` for `NOW`, all inside the `BEGIN TRY ... COMMIT TRANSACTION` block.

## Notes

- Object files hold `CREATE PROCEDURE`. `CREATE OR ALTER` only in migrations.
- The pipeline runs a load procedure from a Script activity of type `Query`, so the row-count result set is returned (`nogamy-build-pipeline`, `references/fabric.md`).
