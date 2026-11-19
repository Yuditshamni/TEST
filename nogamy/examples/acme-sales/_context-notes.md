# Project facts this example assumes

Acme is an invented company. In a real project these facts live in `PROJECT.md` and `_context/` (filled by `nogamy-project-setup`). Here they are one short file, so the example stays small.

## Facts

| # | Fact | Value | Where it lives in a real project |
|---|---|---|---|
| 1 | Platform | SQL Server 2022 (compatibility level 160), T-SQL. No platform pack | `PROJECT.md` → Platform, `_context/platform.md` §2 |
| 2 | Migrations | `python tools/run_migrations.py`, platform `sqlserver`; files split on `GO` lines | `_context/platform.md` §6 |
| 3 | Project prefix | `SALES`, on silver and gold names: `GOLD.SALES_DIM_CUSTOMER`, `SILVER.V_SALES_…`. Bronze is named by its source: `BRONZE.BRONZE_ERP_CUSTOMERS` | `PROJECT.md` → Project rules → Naming |
| 4 | PK / FK / index policy (iron rule, asked once) | none (base default). Uniqueness is proven by `qa/data/` checks. No FK, so a full-reload dimension can `TRUNCATE` | `_context/architecture.md` |
| 5 | Bronze load of ERP `CUSTOMERS` | `FULL` (truncate and reload): the customer number is not unique in the source yet (see the open question). A direct item, no config table: one small table | `sources/acme_erp/README.md` |
| 6 | Gold load of `GOLD.SALES_DIM_CUSTOMER` | full reload. No watermark, no row in `MNG.MNG_BRONZE_GOLD_DELTA` | `stt/sales/SALES_DIM_CUSTOMER.md` |
| 7 | Unknown member | text key `'-99'`, name `N'לא ידוע'`; returned by the silver view (`UNION ALL`) | `nogamy-db-objects` |
| 8 | Types | `nvarchar` for Hebrew business text, `varchar` for ASCII codes, `date`, `datetime2(6)` for ETL columns, `bit` for flags | `_context/platform.md` §10 |

## Business rules (in a real project: `_context/business-rules.md`)

| id | rule_he |
|---|---|
| BR-001 | לקוח שעבר סניף מופיע במערכת ה-ERP פעמיים. השורה העדכנית ביותר (לפי `UPDATED_AT`) קובעת. בתיקו: קוד הסניף הגבוה |
| BR-002 | עיר ריקה או חסרה מוצגת כ"לא ידוע" |
| BR-003 | קוד פלח: `RT` = קמעונאות, `WH` = סיטונאות, כל קוד אחר = לא ידוע |
| BR-004 | לקוח פעיל = סטטוס `A`. כל סטטוס אחר, או סטטוס חסר = לא פעיל |

## Open questions (in a real project: `_context/open-questions.md`)

| id | question | owner | status |
|---|---|---|---|
| OQ-001 | Is (`CUSTOMER_ID`, `BRANCH_CODE`) the real key of ERP `CUSTOMERS`? If yes, bronze can move from `FULL` to `FULL_MERGE` | source owner | open |

## Deviation that exists only in the example

| Base method | Here | Why |
|---|---|---|
| bronze is filled by the bronze load (an ETL item) | migration `0005` inserts eight invented bronze rows | CI runs the example on an empty SQL Server with no source system. A real project never loads data through a migration |
