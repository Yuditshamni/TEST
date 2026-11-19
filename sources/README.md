# sources/ — what exists in the source systems

One folder per source system: a `README.md` for the system, one Markdown file per table, plus `relationships.md`. This is also the **bronze specification**: bronze is the source as is, so a table here plus its load pattern is all bronze needs.

```
sources/
  _template/              copy from here: system.md → <system>/README.md, table.md, relationships.md
  <system>/               README.md, <SOURCE_TABLE>.md, …, relationships.md
```

**Who writes what:** the technical part (type, null %, distinct) is generated with the `nogamy-specs` and `nogamy-explore-data` skills from the data dictionary and a profile query. The systems analyst fills the meaning, the values, `pii` and the notes. Samples are masked or absent.

**Relationships** are the analyst's knowledge: many sources declare no foreign keys. The scripts of the system we replace show which joins were actually used (`nogamy-legacy-migration`).
