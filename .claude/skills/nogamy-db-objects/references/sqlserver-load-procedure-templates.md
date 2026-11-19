# Load procedure templates — SQL Server / Azure SQL Database

Part of `nogamy-db-objects`. Read when `_context/platform.md` §2 names SQL Server or Azure SQL Database. The same frame as `load-procedure-templates.md`, in T-SQL. The same on both platforms.

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
    SET XACT_ABORT ON;
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

## Delta, match by key (example: `SILVER.SP_SALES_FACT_ORDERS`)

Same header, `SET` lines, `@NOW` and `CATCH` block as the full reload. The body inside `BEGIN TRANSACTION ... COMMIT TRANSACTION`:

```sql
        -- 1. silver staging: as above, plus LOAD_TO_BRONZE_TS
        TRUNCATE TABLE SILVER.SILVER_SALES_FACT_ORDERS;
        INSERT INTO SILVER.SILVER_SALES_FACT_ORDERS (FACT_KEY, ..., IS_LAST_UPDATE_IND, ETL_INSERT_DATE, LOAD_TO_BRONZE_TS)
        SELECT FACT_KEY, ..., 1, @NOW, LOAD_TO_BRONZE_TS
        FROM SILVER.V_SALES_FACT_ORDERS_FINAL_STEP;

        -- 2. gold: replace by key
        UPDATE GOLD.SALES_FACT_ORDERS SET IS_LAST_UPDATE_IND = 0 WHERE IS_LAST_UPDATE_IND = 1;

        DELETE g
        FROM GOLD.SALES_FACT_ORDERS AS g
        WHERE EXISTS (SELECT 1 FROM SILVER.SILVER_SALES_FACT_ORDERS AS s WHERE s.FACT_KEY = g.FACT_KEY);

        INSERT INTO GOLD.SALES_FACT_ORDERS (FACT_KEY, ..., IS_LAST_UPDATE_IND, ETL_INSERT_DATE, ETL_UPDATE_DATE)
        SELECT FACT_KEY, ..., 1, ETL_INSERT_DATE, @NOW
        FROM SILVER.SILVER_SALES_FACT_ORDERS;

        -- 3. watermark (nogamy-bronze-load), inside the same transaction
        UPDATE MNG.MNG_BRONZE_GOLD_DELTA
        SET MAX_CONFIRMED_BRONZE_TS = COALESCE((SELECT MAX(LOAD_TO_BRONZE_TS) FROM SILVER.SILVER_SALES_FACT_ORDERS),
                                               MAX_CONFIRMED_BRONZE_TS),
            ETL_UPDATE_DATE = @NOW
        WHERE BRONZE_TABLE_NAME = 'BRONZE.BRONZE_ERP_ORDERS' AND GOLD_TABLE_NAME = 'GOLD.SALES_FACT_ORDERS';
```

A delta dimension also inserts its `-99` row when missing, inside the same transaction:

```sql
        IF NOT EXISTS (SELECT 1 FROM GOLD.SALES_DIM_PRODUCT WHERE KEY_PRODUCT = -99)
            INSERT INTO GOLD.SALES_DIM_PRODUCT (KEY_PRODUCT, PRODUCT_NAME, ..., IS_LAST_UPDATE_IND, ETL_INSERT_DATE, ETL_UPDATE_DATE)
            VALUES (-99, N'לא ידוע', ..., 1, @NOW, @NOW);
```

## Notes

- Object files hold `CREATE PROCEDURE`. `CREATE OR ALTER` only in migrations, with `GO` before it.
- `TRUNCATE` rolls back with the transaction. It is refused on a table referenced by a `FOREIGN KEY`: such a table reloads with `DELETE` (`references/sqlserver.md`).
- `SET XACT_ABORT ON`: a run-time error rolls back the whole transaction; `THROW` re-raises the original error to the caller.
- The statement before `THROW` must end with `;`.
- Hebrew literals need `N'...'`.
- A `MERGE` variant (delta, merge): end it with `;`, and make the source unique on the key first; one target row matched by two source rows is an error.

## Sources

- https://learn.microsoft.com/en-us/sql/t-sql/statements/truncate-table-transact-sql
- https://learn.microsoft.com/en-us/sql/t-sql/statements/set-xact-abort-transact-sql
- https://learn.microsoft.com/en-us/sql/t-sql/language-elements/try-catch-transact-sql
- https://learn.microsoft.com/en-us/sql/t-sql/language-elements/throw-transact-sql
- https://learn.microsoft.com/en-us/sql/t-sql/statements/merge-transact-sql
- https://learn.microsoft.com/en-us/sql/t-sql/data-types/nchar-and-nvarchar-transact-sql
