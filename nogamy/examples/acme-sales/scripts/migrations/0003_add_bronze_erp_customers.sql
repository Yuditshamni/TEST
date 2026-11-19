-- migration: 0003
-- PR: example
-- Creates the bronze table BRONZE.BRONZE_ERP_CUSTOMERS (ERP CUSTOMERS as is + ETL columns), only if it does not exist.

--------------------------------------------------------
-- BRONZE.BRONZE_ERP_CUSTOMERS
-- ERP CUSTOMERS as is + the bronze ETL columns. Load pattern FULL (truncate and reload): no trusted key yet (OQ-001).
-- Source columns keep the source types and nullability (sources/acme_erp/CUSTOMERS.md). No business logic.
-- No DELETED_DATE: a FULL table drops a deleted row with the truncate.
--------------------------------------------------------
IF OBJECT_ID(N'BRONZE.BRONZE_ERP_CUSTOMERS', N'U') IS NULL
CREATE TABLE BRONZE.BRONZE_ERP_CUSTOMERS
(
    CUSTOMER_ID                   VARCHAR(10)   NULL,
    BRANCH_CODE                   VARCHAR(5)    NULL,
    CUSTOMER_NAME                 NVARCHAR(100) NULL,
    CITY_NAME                     NVARCHAR(50)  NULL,
    SEGMENT_CODE                  VARCHAR(2)    NULL,
    STATUS_CODE                   VARCHAR(1)    NULL,
    CREATED_DATE                  DATE          NULL,
    UPDATED_AT                    DATETIME2(0)  NULL,
    LOAD_TO_BRONZE_TS             DATETIME2(6)  NOT NULL,
    IS_LAST_INSERT_TO_BRONZE_IND  BIT           NOT NULL,
    ETL_INSERT_DATE               DATETIME2(6)  NOT NULL,
    ETL_UPDATE_DATE               DATETIME2(6)  NOT NULL
);
GO
