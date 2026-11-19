# architecture.md — current truth

What is decided, as it stands now. Rationale and history: `decisions-log.md`. Open items: `open-questions.md`. Platform facts (stack, environments, Git, promotion, AI access): `platform.md`.
A contradiction between code and this file = stop and ask. A new decision = update this file and add a line to the decisions log (`nogamy-project-memory`).

---

## 1. Data architecture

| Topic | Decision |
|---|---|
| Storage | ? |
| Layers / schemas | method default: `BRONZE` (source as is), `SILVER` (business logic), `GOLD` (star model), `MNG` (config, watermark). Deviations: "Deviations from the base" below |
| Ingestion | ? |
| Transformation | ? |
| Orchestration | ? |
| Incremental loads and source deletes | ? (`nogamy-bronze-load`) |
| Data quality | ? (`nogamy-qa-checks`) |
| Reporting | ? (`nogamy-semantic-model`) |
| PK / FK / index policy (asked once, before the first gold table) | ? |

## 2. Not chosen

Options considered and rejected, one line each with the reason. Saves the next person from proposing them again.

## 3. Sources

Known source systems (list not closed). Per-source access, authentication and load pattern: `sources/<system>/README.md`.

## 4. Model

Filled per table from `stt/` once approved.

| Table | Type | Grain | Load |
|---|---|---|---|

## 5. Deviations from the base

The project's deviations from Nogamy's base method (`nogamy-method`). One row each; a rule that binds the agents also goes to `PROJECT.md` → Project rules.

| # | Base rule | This project | Reason | Decided by, date |
|---|---|---|---|---|

## 6. Not used

Folders or parts of the core this project does not use (e.g. `bi/`, or `db/` `etl/` when the platform's own layout replaces them).

| Folder / part | Why |
|---|---|