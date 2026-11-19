# Load procedure templates

Part of `nogamy-db-objects` ("Load procedure"). Open when writing or changing a load procedure. Plain SQL: transaction, error handling and "now" are written in the project's dialect (`nogamy-write-sql`; on Fabric: `fabric-load-procedure-templates.md`).

## Full reload (example: `SILVER.SP_SALES_DIM_CUSTOMER`)

```sql
--------------------------------------------------------
-- SILVER.SP_SALES_DIM_CUSTOMER
-- Loads GOLD.SALES_DIM_CUSTOMER: view -> silver staging -> gold. Full reload. Idempotent.
--------------------------------------------------------
-- NOW = one timestamp for the whole run, in UTC
BEGIN TRANSACTION;

    -- 1. silver staging: freeze this load
    TRUNCATE TABLE SILVER.SILVER_SALES_DIM_CUSTOMER;
    INSERT INTO SILVER.SILVER_SALES_DIM_CUSTOMER (KEY_CUSTOMER, …, IS_LAST_UPDATE_IND, ETL_INSERT_DATE)
    SELECT KEY_CUSTOMER, …, 1, NOW
    FROM SILVER.V_SALES_DIM_CUSTOMER;

    -- 2. gold: full reload from staging
    TRUNCATE TABLE GOLD.SALES_DIM_CUSTOMER;
    INSERT INTO GOLD.SALES_DIM_CUSTOMER (KEY_CUSTOMER, …, IS_LAST_UPDATE_IND, ETL_INSERT_DATE, ETL_UPDATE_DATE)
    SELECT KEY_CUSTOMER, …, IS_LAST_UPDATE_IND, ETL_INSERT_DATE, NOW
    FROM SILVER.SILVER_SALES_DIM_CUSTOMER;

COMMIT;
-- on any error: ROLLBACK, raise the error
-- result: SILVER_ROWS = COUNT(*) of staging, GOLD_ROWS = COUNT(*) of gold
```

An empty bronze would empty gold: the bronze gate (`Empty_Table`) runs before, so the procedure never sees an empty source.

## Delta, match by key (base §4.12, company standard)

Same frame as the full reload; step 2 and the watermark change:

```sql
-- 1. silver staging: as above, plus LOAD_TO_BRONZE_TS

-- 2. gold: replace by key
UPDATE GOLD.SALES_FACT_ORDERS SET IS_LAST_UPDATE_IND = 0 WHERE IS_LAST_UPDATE_IND = 1;
DELETE FROM GOLD.SALES_FACT_ORDERS
WHERE EXISTS (SELECT 1 FROM SILVER.SILVER_SALES_FACT_ORDERS AS S
              WHERE S.FACT_KEY = GOLD.SALES_FACT_ORDERS.FACT_KEY);
INSERT INTO GOLD.SALES_FACT_ORDERS (…, IS_LAST_UPDATE_IND, ETL_INSERT_DATE, ETL_UPDATE_DATE)
SELECT …, 1, ETL_INSERT_DATE, NOW FROM SILVER.SILVER_SALES_FACT_ORDERS;

-- 3. watermark (nogamy-bronze-load), inside the same transaction
UPDATE MNG.MNG_BRONZE_GOLD_DELTA
SET MAX_CONFIRMED_BRONZE_TS = COALESCE((SELECT MAX(LOAD_TO_BRONZE_TS) FROM SILVER.SILVER_SALES_FACT_ORDERS),
                                       MAX_CONFIRMED_BRONZE_TS),
    ETL_UPDATE_DATE = NOW
WHERE BRONZE_TABLE_NAME = 'BRONZE.BRONZE_ERP_ORDERS' AND GOLD_TABLE_NAME = 'GOLD.SALES_FACT_ORDERS';
```

- `COALESCE` keeps the old watermark when the load was empty.
- The delta procedure also inserts the `-99` row if it is missing.
