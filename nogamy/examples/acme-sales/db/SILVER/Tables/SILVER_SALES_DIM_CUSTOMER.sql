--------------------------------------------------------
-- SILVER.SILVER_SALES_DIM_CUSTOMER
-- Silver staging of GOLD.SALES_DIM_CUSTOMER: freezes one load. The gold columns without ETL_UPDATE_DATE.
-- No LOAD_TO_BRONZE_TS: full reload, no watermark. Emptied and filled by SILVER.SP_SALES_DIM_CUSTOMER.
--------------------------------------------------------
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
