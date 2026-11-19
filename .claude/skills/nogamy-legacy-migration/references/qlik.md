# nogamy-legacy-migration — Qlik

Read when `PROJECT.md` → Identity → `Replaces` names Qlik (QlikView or Qlik Sense).

## Inputs (read-only, `_private/raw/reference/qlik-metadata/`)

The Qlik export, one folder per app, converted to Markdown:

| File | Holds |
|---|---|
| `<App>/<App>_Script.md` | the load script: sources, transformations, filters |
| `<App>/ERD_<App>_Script.md` | the app's data model: tables and keys |
| `<App>/DB_<App>_script.md` | what the app reads from the BI database |
| `<App>/<App>_Metadata.md` | dimensions, measures, expressions, sheets |
| `<SHARED_DIMS> - SCRIPT.md` | shared dimension logic, reused by several apps |
| `<QLIK DB>.md` | the BI database tables Qlik reads |
| `_private/raw/reference/<AS-IS model map>.md` | the client's own map of the existing model |

## Steps on Qlik

The skill's steps, one Qlik app at a time:

- Sources: `used_by_legacy: <App>` (older projects wrote `used_by_qlik`).
- Rules: every filter, mapping or `IF` in the load script; source: `Qlik <App>, <script section>`.
- Measures: every expression in `<App>_Metadata.md` → `_context/legacy-measures.md`, the expression as is (set analysis included). An older project may hold them in `_context/qlik-measures.md` (columns `app · sheet · measure_name · expression · meaning_he · in_use · target_measure`): read it as the same table.
- STT drafts: a "from Qlik" note per column.

## Measures to DAX (when the BI tool is Power BI)

`nogamy-semantic-model` drafts DAX from the rows with `in_use = yes`, with the Qlik expression and the meaning in the measure's description. Every draft is for the Power BI developer to approve.
