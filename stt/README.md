# stt/ — what we build

Source-to-Target specification. One Markdown file per **target table**, one folder per domain, plus `relationships.md` for the star model.
This is the single source of truth: table definitions, loads, data checks and the semantic model descriptions are derived from it. The file for client sign-off is **exported** from here (`nogamy-specs` skill), never edited back.

```
stt/
  _template/        copy from here
  <domain>/         <PROJECT>_DIM_<ENTITY>.md, <PROJECT>_FACT_<SUBJECT>.md, relationships.md
```

| Column | Who fills it |
|---|---|
| target_column, source_table, source_column, description_he, synonyms_he, pii | systems analyst |
| type, transformation (technical detail), load pattern | data engineer |

Only a table with `status: approved` gets built. The order of the tables in the domain is the build order: dimensions before facts.
