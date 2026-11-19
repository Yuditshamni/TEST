# nogamy-naming — Microsoft Fabric

Read when `_context/platform.md` §2 names Fabric. Names and paths that exist only on Fabric, plus the defaults the Fabric pack ships with. The rules in `SKILL.md` still hold; a project choice still goes in `PROJECT.md` → Project rules → Naming.

## Why exact spelling matters more here

The Fabric Warehouse is **case sensitive** (`Latin1_General_100_BIN2_UTF8`) for object names and data: one exact spelling per name, everywhere, `UPPER_SNAKE_CASE` in the warehouse. References are two-part only (`SCHEMA.OBJECT`), never `WAREHOUSE.SCHEMA.OBJECT`.

## Fabric items

| Object | Pattern | Example | Source |
|---|---|---|---|
| warehouse | `WH_<SCOPE>`, same name in every workspace | `WH_DWH` | P (pack default) |
| quality framework schema | `QA`: `QA.QA_DQA_QUERY`, `QA.QA_DQA_RESULT`, `QA.SP_DQA` (the base keeps them in `MNG`) | | pack default, to confirm per project |
| variable library | `VL_<Name>` | `VL_DWH` | P (pack default) |
| pipeline | as `SKILL.md` → ETL items (`PL_…`, `GPL_…`); folder `<name>.DataPipeline/pipeline-content.json` | `PL_Run_Sales_Gold.DataPipeline` | N |
| roles | SERVE views only where the Power BI model needs them (it reads `GOLD` by default), no Blob pipelines on Fabric | | N |
| connection placeholder in pipeline JSON | `__<PURPOSE>_CONNECTION__` | `__FABRIC_PIPELINES_CONNECTION__` | P (pack) |
| try-out pipeline | workspace folder `pipelines/TRY` | | P |

## Repo paths on Fabric

| Item | Pattern | Example |
|---|---|---|
| warehouse object file | `fabric/data/WH_DWH.Warehouse/<SCHEMA>/<Tables\|Views\|StoredProcedures\|Functions>/<OBJECT>.sql` | `…/GOLD/Tables/SALES_DIM_CUSTOMER.sql` |
| pipeline folders | `fabric/data/pipelines/<project>/00_orchestration`, `01_bronze`, `02_silver`, `03_gold`, `04_qa`; shared by all projects: `fabric/data/pipelines/_shared/` | |
| pipeline list | `fabric/data/pipelines/<project>/README.md` | |
| semantic model / report | `fabric/bi/<project>/<name>.SemanticModel/` (TMDL), `fabric/bi/<project>/<name>.Report/` (PBIR) | |
