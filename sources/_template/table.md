# <SOURCE_TABLE_NAME>

system: <system>   schema: <schema>   rows: ~<n>   columns: <n>
pk: <columns>   change_column: <column that moves on every change>   refresh: <nightly / API / …>   history: <current only / rows per period>
load_pattern: <FULL | FULL_MERGE | DELTA | …>   bronze_table: <BRONZE.BRONZE_<SYSTEM>_<TABLE>>   (`nogamy-bronze-load` skill)
used_by_legacy: <apps / reports>   owner_business: <role>   owner_technical: <DBA>   status: draft

description_he: <משפט או שניים: מה הטבלה מייצגת, מי משתמש בה>

> Technical columns come from the profile (`nogamy-explore-data`), counts only. The analyst fills `meaning_he`, `values_he`, `pii`, `notes`.
> Unknown = `לא ידוע`. Empty = not checked yet. Open questions go to `_context/open-questions.md`.

## Columns

| # | column | type | nullable | key | null_pct | distinct | meaning_he | values_he | pii | notes |
|---|---|---|---|---|---|---|---|---|---|---|
| 1 | | | | | | | | | | |

## Notes

- Known quirks, orphan rates, codes that changed over time.
