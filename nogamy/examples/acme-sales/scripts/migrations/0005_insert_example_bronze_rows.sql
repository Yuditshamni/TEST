-- migration: 0005
-- PR: example
-- Inserts eight invented ERP customer rows into BRONZE.BRONZE_ERP_CUSTOMERS so the example runs without a source (example only: in a project the bronze load fills bronze).

--------------------------------------------------------
-- Test data, invented. What each row shows:
--   C-1005 twice (moved from BR01 to BR03): BR-001 keeps the BR03 row (latest UPDATED_AT)
--   C-1003 NULL city, C-1004 empty city: both become N'לא ידוע' (BR-002)
--   C-1006 segment XX: not in the list, becomes N'לא ידוע' (BR-003)
--   C-1004, C-1007 status I: IS_ACTIVE_IND = 0 (BR-004)
-- Safe twice: a row is inserted only if its source key (CUSTOMER_ID, BRANCH_CODE) is not in bronze yet.
--------------------------------------------------------
DECLARE @NOW DATETIME2(6) = CAST(SYSUTCDATETIME() AS DATETIME2(6));

INSERT INTO BRONZE.BRONZE_ERP_CUSTOMERS
(
    CUSTOMER_ID,
    BRANCH_CODE,
    CUSTOMER_NAME,
    CITY_NAME,
    SEGMENT_CODE,
    STATUS_CODE,
    CREATED_DATE,
    UPDATED_AT,
    LOAD_TO_BRONZE_TS,
    IS_LAST_INSERT_TO_BRONZE_IND,
    ETL_INSERT_DATE,
    ETL_UPDATE_DATE
)
SELECT
    V.CUSTOMER_ID,
    V.BRANCH_CODE,
    V.CUSTOMER_NAME,
    V.CITY_NAME,
    V.SEGMENT_CODE,
    V.STATUS_CODE,
    CAST(V.CREATED_DATE AS DATE),
    CAST(V.UPDATED_AT AS DATETIME2(0)),
    @NOW,
    1,
    @NOW,
    @NOW
FROM (VALUES
    ('C-1001', 'BR01', N'חנות לדוגמה 01', N'תל אביב',  'RT', 'A', '2024-01-15', '2026-03-01 09:00:00'),
    ('C-1002', 'BR01', N'חנות לדוגמה 02', N'חיפה',     'WH', 'A', '2024-02-20', '2026-01-12 14:30:00'),
    ('C-1003', 'BR02', N'חנות לדוגמה 03', NULL,        'RT', 'A', '2024-05-02', '2025-11-30 08:15:00'),
    ('C-1004', 'BR02', N'חנות לדוגמה 04', N'',         'RT', 'I', '2024-07-09', '2025-12-01 10:00:00'),
    ('C-1005', 'BR01', N'חנות לדוגמה 05', N'ירושלים',  'WH', 'A', '2024-03-18', '2025-06-01 12:00:00'),
    ('C-1005', 'BR03', N'חנות לדוגמה 05', N'באר שבע',  'WH', 'A', '2024-03-18', '2026-02-10 16:45:00'),
    ('C-1006', 'BR03', N'חנות לדוגמה 06', N'אילת',     'XX', 'A', '2025-01-05', '2026-02-28 11:20:00'),
    ('C-1007', 'BR02', N'חנות לדוגמה 07', N'נתניה',    'RT', 'I', '2025-04-22', '2026-04-03 13:05:00')
) AS V (CUSTOMER_ID, BRANCH_CODE, CUSTOMER_NAME, CITY_NAME, SEGMENT_CODE, STATUS_CODE, CREATED_DATE, UPDATED_AT)
WHERE NOT EXISTS (SELECT 1
                  FROM BRONZE.BRONZE_ERP_CUSTOMERS AS B
                  WHERE B.CUSTOMER_ID = V.CUSTOMER_ID
                    AND B.BRANCH_CODE = V.BRANCH_CODE);
GO
