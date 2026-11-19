--------------------------------------------------------
-- SILVER.V_SALES_DIM_CUSTOMER_STEP1_SOURCE
-- Step 1 of 2 for GOLD.SALES_DIM_CUSTOMER (full reload): the source columns, the bronze filter,
-- and the rank of each row inside its customer (BR-001: latest UPDATED_AT first, then the higher BRANCH_CODE).
-- Why two views: keeping only rank 1 needs the rank computed first, so the filter sits in the next view.
-- Reads only its own bronze table.
--------------------------------------------------------
CREATE VIEW SILVER.V_SALES_DIM_CUSTOMER_STEP1_SOURCE
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
