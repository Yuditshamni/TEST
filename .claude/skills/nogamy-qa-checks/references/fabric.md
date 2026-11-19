# nogamy-qa-checks — Microsoft Fabric

Read when `_context/platform.md` §2 names Fabric. The checks in `SKILL.md` are the same; this file says where the framework lives and how checks run on the Fabric Warehouse.

Needs the Fabric pack (`tools/fabric/`, `tools/migrate/`, `PROJECT.md` → `Packs: fabric`). Missing → run `nogamy-add-pack` first.

## Running checks

- Per-table checks: `python tools/fabric/wh_sql.py <server> WH_DWH @qa/data/<file>.sql` (DEV, as the AI identity). Then run the load again and the checks again.
- The SQL is T-SQL (`nogamy-write-sql` → `references/fabric.md`): `TOP (n)`, `LEN`, case-sensitive comparisons. A person's look at 100 rows: `SELECT TOP 100 ...`, run by the person, never by the AI on sensitive columns.

## The quality framework on Fabric

The Fabric pack ships it in the `QA` schema (the base keeps it in `MNG`; status in `nogamy-naming`):

| Object | File |
|---|---|
| `QA.QA_DQA_QUERY` | `fabric/data/WH_DWH.Warehouse/QA/Tables/QA_DQA_QUERY.sql` |
| `QA.QA_DQA_RESULT` | `fabric/data/WH_DWH.Warehouse/QA/Tables/QA_DQA_RESULT.sql` |
| `QA.SP_DQA` | `fabric/data/WH_DWH.Warehouse/QA/StoredProcedures/SP_DQA.sql` |

- Read the gate in pipelines: the shared pipeline `GPL_DQA` (`fabric/data/pipelines/_shared/GPL_DQA.DataPipeline/`) calls `QA.SP_DQA`; a failed check raises error 50001, so the activity fails and the pipeline stops. Examples: `EXEC QA.SP_DQA @GROUP_NAME = 'Sales_GOLD_Dims';` · `EXEC QA.SP_DQA @DQA_TYPE = 'Duplicates', @TABLE_NAME = 'PRE_BRONZE.PRE_BRONZE_CRM_CUSTOMERS', @TABLE_KEYS = 'CUSTOMER_ID';`
- Gates per `nogamy-build-pipeline` → `references/fabric.md`: after each bronze load (in `PL_<Source>_To_Bronze`), after `Finish Dims`, after `Finish Facts`.

## Golden questions

On Fabric the AI assistant that answers from the semantic model is the Fabric Data Agent: ask it each golden question before a release. A wrong answer is fixed in the model, never in the agent's instructions.
