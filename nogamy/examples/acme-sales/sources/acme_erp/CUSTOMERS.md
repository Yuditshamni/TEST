# CUSTOMERS

system: acme_erp   schema: erp   rows: ~8   columns: 8
pk: none trusted (unique on `CUSTOMER_ID` + `BRANCH_CODE`, OQ-001)   change_column: `UPDATED_AT` (not proven)   refresh: nightly   history: current only, plus the old row of a customer who moved branch
load_pattern: FULL   bronze_table: BRONZE.BRONZE_ERP_CUSTOMERS   (`nogamy-bronze-load` skill)
used_by_legacy: the monthly sales report (customer list)   owner_business: sales operations manager   owner_technical: ERP DBA   status: approved

description_he: רשימת הלקוחות של אקמה (חנויות), עם הסניף שמטפל בהן, העיר, הפלח והסטטוס.

> Technical columns come from the profile (`nogamy-explore-data`), counts only. The analyst fills `meaning_he`, `values_he`, `pii`, `notes`.
> Unknown = `לא ידוע`. Empty = not checked yet. Open questions go to `_context/open-questions.md`.

## Columns

| # | column | type | nullable | key | null_pct | distinct | meaning_he | values_he | pii | notes |
|---|---|---|---|---|---|---|---|---|---|---|
| 1 | CUSTOMER_ID | varchar(10) | yes | business key (not unique, finding 1) | 0 | 7 | מספר לקוח | `C-` ואחריו ארבע ספרות | no | 2 rows for one customer who moved branch |
| 2 | BRANCH_CODE | varchar(5) | yes | part of the unique pair | 0 | 3 | קוד הסניף שמטפל בלקוח | `BR01`–`BR03` | no | |
| 3 | CUSTOMER_NAME | nvarchar(100) | yes | | 0 | 7 | שם הלקוח (שם החנות) | | yes | a sole trader's store name is a person's name |
| 4 | CITY_NAME | nvarchar(50) | yes | | 12.5 | 7 | עיר החנות | | no | NULL and empty string both mean "no city" (finding 2) |
| 5 | SEGMENT_CODE | varchar(2) | yes | | 0 | 3 | פלח לקוח | `RT` = קמעונאות, `WH` = סיטונאות | no | 1 row with `XX` (finding 3) |
| 6 | STATUS_CODE | varchar(1) | yes | | 0 | 2 | סטטוס לקוח | `A` = פעיל, `I` = לא פעיל | no | |
| 7 | CREATED_DATE | date | yes | | 0 | 7 | תאריך פתיחת הלקוח | | no | |
| 8 | UPDATED_AT | datetime2(0) | yes | | 0 | 8 | מועד העדכון האחרון של השורה | | no | used to pick the latest row (BR-001) |

## Notes

- No row has a NULL `CUSTOMER_ID` in the profile. Silver still excludes such a row: gold has no NULL key.
- `null_pct` and `distinct` are counted on the example's bronze rows (migration `0005`).
