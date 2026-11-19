# SALES_DIM_CUSTOMER

layer: gold   schema: GOLD   grain: one row per customer (`CUSTOMER_ID`), plus the `-99` row   load: Full
business_key: CUSTOMER_ID   source_systems: acme_erp   owner: systems analyst   status: approved   built: 2026-11-10, example
description_he: הלקוחות של אקמה: שורה אחת לכל לקוח, עם הסניף, העיר, הפלח והאם הוא פעיל.

Names: `nogamy-naming` skill. Status `approved` = ready to build. Open questions go to `_context/open-questions.md`, not here.

## Columns

| target_column | type | source_table | source_column | transformation | description_he | synonyms_he | pii |
|---|---|---|---|---|---|---|---|
| KEY_CUSTOMER | varchar(10) | BRONZE.BRONZE_ERP_CUSTOMERS | CUSTOMER_ID | business key of the entity, as is; `'-99'` = unknown | מספר לקוח | קוד לקוח, מס' לקוח | no |
| CUSTOMER_NAME | nvarchar(100) | BRONZE.BRONZE_ERP_CUSTOMERS | CUSTOMER_NAME | spaces trimmed at both ends; `-99` row: "לא ידוע" | שם הלקוח | שם חנות, לקוח | yes |
| BRANCH_CODE | varchar(5) | BRONZE.BRONZE_ERP_CUSTOMERS | BRANCH_CODE | as is, from the row chosen by BR-001; `-99` row: `'-99'` | הסניף שמטפל בלקוח | סניף, סניף מטפל | no |
| CITY_NAME | nvarchar(50) | BRONZE.BRONZE_ERP_CUSTOMERS | CITY_NAME | spaces trimmed; NULL or empty → "לא ידוע" (BR-002) | עיר הלקוח | עיר, יישוב, מיקום | no |
| SEGMENT_NAME | nvarchar(30) | BRONZE.BRONZE_ERP_CUSTOMERS | SEGMENT_CODE | `RT` → "קמעונאות", `WH` → "סיטונאות", anything else or NULL → "לא ידוע" (BR-003) | פלח הלקוח | פלח, סוג לקוח, ערוץ | no |
| IS_ACTIVE_IND | bit | BRONZE.BRONZE_ERP_CUSTOMERS | STATUS_CODE | `A` → 1, anything else or NULL → 0 (BR-004); `-99` row: 0 | האם הלקוח פעיל | לקוח פעיל, פעיל | no |
| CUSTOMER_CREATED_DATE | date | BRONZE.BRONZE_ERP_CUSTOMERS | CREATED_DATE | as is; `-99` row: NULL (a date has no "unknown" value) | תאריך פתיחת הלקוח | תאריך הצטרפות, לקוח מאז | no |
| IS_LAST_UPDATE_IND | bit | | | ETL column: always 1 (full reload) | שורה עדכנית | | no |
| ETL_INSERT_DATE | datetime2(6) | | | ETL column: when this load froze the row in silver staging (UTC) | מועד טעינה | | no |
| ETL_UPDATE_DATE | datetime2(6) | | | ETL column: when this load wrote the row to gold (UTC) | מועד עדכון | | no |

## Dimension joins (facts only)

None: this is a dimension.

## Filters and sources

- Bronze rows with `IS_LAST_INSERT_TO_BRONZE_IND = 1` only (every row, in this `FULL` bronze).
- Rows with a NULL `CUSTOMER_ID` are excluded: gold has no NULL key (none in the profile).
- One source. Two rows for one customer (moved branch): one row kept, by BR-001.

## Business rules

- BR-001: the latest row per `CUSTOMER_ID` by `UPDATED_AT` wins; on a tie, the higher `BRANCH_CODE`.
- BR-002: empty or missing city → "לא ידוע".
- BR-003: segment code → segment name.
- BR-004: active = status `A`.
