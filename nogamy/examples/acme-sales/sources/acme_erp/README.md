# Acme ERP

type: SQL Server database (invented)   owner_business: sales operations manager   owner_technical: ERP DBA   status: approved
code in object names: `ERP` (`BRONZE.BRONZE_ERP_<TABLE>`)
description_he: מערכת ה-ERP של אקמה. מנהלת לקוחות, הזמנות וחשבוניות. משתמשים בה אנשי המכירות והכספים.

## Access

| Topic | Value |
|---|---|
| How we connect (driver, gateway, API, file drop) | SQL Server driver, read-only account, from the ETL tool |
| Account and its rights (no passwords here) | a read-only reader account on the ERP schema; secret in the credential store |
| Environment we read from (production / copy / test) | a nightly copy of production |
| Sensitive data in this source | customer names (a store can be a sole trader: treated as a person's name) |
| Refresh: when the source itself is updated | the copy is refreshed nightly |
| Limits (rate, window, size) | none known for `CUSTOMERS` (small table) |

## Load

| Topic | Value |
|---|---|
| Load pattern for the system (`nogamy-bronze-load`) | `FULL` for `CUSTOMERS` until OQ-001 is answered; then `FULL_MERGE` |
| Config-driven or a direct pipeline, and why | direct: one small table; a config table buys nothing yet |
| How the source signals a deleted row | it does not: a customer is set to status `I`, never deleted |
| Change column that can be trusted | `UPDATED_AT`: not proven to move on every change, so no `DELTA` |

## Tables

| Table | Rows | Load | Spec | Status |
|---|---|---|---|---|
| CUSTOMERS | ~8 (example data) | FULL | `CUSTOMERS.md` | approved |

## Findings

1. A customer who moved to another branch keeps the old row: `CUSTOMER_ID` is not unique (profile: 8 rows, 7 distinct `CUSTOMER_ID`; unique on `CUSTOMER_ID` + `BRANCH_CODE`). Handled in silver by BR-001; OQ-001 asks the source owner.
2. `CITY_NAME` holds both NULL and an empty string for "no city" (profile: 1 NULL, 1 empty of 8). Both become "לא ידוע" in silver (BR-002).
3. `SEGMENT_CODE` has a value outside the documented list (`XX`, 1 row). Mapped to "לא ידוע" (BR-003).
