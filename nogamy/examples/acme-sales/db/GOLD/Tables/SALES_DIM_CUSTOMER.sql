--------------------------------------------------------
-- GOLD.SALES_DIM_CUSTOMER
-- Customer dimension. Grain: one row per customer (KEY_CUSTOMER), plus the '-99' row. Full reload.
-- Spec: stt/sales/SALES_DIM_CUSTOMER.md. Loaded by SILVER.SP_SALES_DIM_CUSTOMER.
-- No PK (project policy: none); uniqueness is proven by qa/data/SALES_DIM_CUSTOMER.sql.
--------------------------------------------------------
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
