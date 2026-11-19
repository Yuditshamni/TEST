# nogamy-method — Microsoft Fabric

Read when `_context/platform.md` §2 names Fabric. The method is the same; this is how its layers usually land on Fabric.
These are defaults seen on Fabric projects, not decisions: each one the project takes is a row in its own deviations table (`_context/architecture.md`).

## Layers on Fabric

| Base | On Fabric |
|---|---|
| all layers | schemas in one Fabric Warehouse, `WH_DWH`, the same name in every workspace (`PROJECT.md` → Environments) |
| PRE_BRONZE | usually not needed: the Data Factory Copy activity lands in `BRONZE` directly. Only for a source that re-delivers keys |
| BRONZE | `BRONZE`: source as is + ETL columns (`nogamy-bronze-load`) |
| SILVER | `SILVER`: views + silver staging tables, loaded by a stored procedure (`nogamy-db-objects`) |
| GOLD | `GOLD`: the star model the Power BI semantic model reads |
| SERVE | optional `SERVE` schema of views on `GOLD`; by default the Power BI semantic model reads `GOLD` |
| MNG | `MNG`: config (`MNG_BRONZE_CONFIGURATION`), watermark (`MNG_BRONZE_GOLD_DELTA`), migration log (`MNG_MIGRATION_LOG`) |
| QA | often a `QA` schema for the data-quality framework (`fabric/data/WH_DWH.Warehouse/QA/`, `nogamy-qa-checks`) |

## Deviations Fabric projects often take

- One file per object in `fabric/data/WH_DWH.Warehouse/<SCHEMA>/...` + a numbered migration per change in `scripts/migrations/`, applied by `tools/migrate/run_migrations.py` (`nogamy-db-objects`, `nogamy-deploy`).
- Promotion of pipelines and migrations by a CI runner (for example GitHub Actions), not by hand (`nogamy-deploy`).
- Bronze delta loads with `MERGE` (`nogamy-bronze-load`).

## Where each topic lives — Fabric parts

Each skill below has its own `references/fabric.md`: `nogamy-naming` (pipeline and activity names, Data Factory methodology §1), `nogamy-db-objects` (Warehouse T-SQL), `nogamy-build-pipeline` (Data Factory pipelines, Variable library), `nogamy-semantic-model` (TMDL / PBIR), `nogamy-dev-workflow` (the agent runs the DEV loop with `tools/fabric`).
