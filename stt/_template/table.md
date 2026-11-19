# <PROJECT>_<DIM|FACT>_<ENTITY>

layer: gold   schema: GOLD   grain: <one row per …>   load: <Full | Delta by key | MERGE | SCD2 | Append>
business_key: <columns>   source_systems: <systems>   owner: <analyst>   status: draft   built: <date, branch — filled by build-table>
description_he: <משפט אחד: מה הטבלה מייצגת>

Names: `nogamy-naming` skill. Status `approved` = ready to build. Open questions go to `_context/open-questions.md`, not here.

## Columns

| target_column | type | source_table | source_column | transformation | description_he | synonyms_he | pii |
|---|---|---|---|---|---|---|---|
| KEY_<ENTITY> | | | | business key of the entity; `-99` = unknown | מפתח | | |
| | | | | | | | |

For a fact: `FACT_KEY` first, then one `KEY_<ENTITY>` per dimension (same name as in the dimension), then measures.
Transformation is written in words; the code is derived from it.

## Dimension joins (facts only)

| KEY_<ENTITY> | dimension | join on | SCD2: which version | not found |
|---|---|---|---|---|
| | | | | `-99` |

## Filters and sources

- Rows excluded, and why.
- More than one source for the same entity: which wins, and how they are matched.

## Business rules

- BR-xxx (see `_context/business-rules.md`): …
