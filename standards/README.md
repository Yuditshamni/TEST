# standards/ — Nogamy's organizational method

The originals live here, in the starter. Inside a project this folder is **read-only**: it holds the version the project was started with.

| File | What | Applies to |
|---|---|---|
| `base_prompt.md` | The DWH Engineering Assistant base prompt: iron rules, milestones, layer standards, procedure templates. The top layer of the method | every project |
| `ADF_Best_Practices_Methodology.md` | Nogamy's pipeline methodology, written for Azure Data Factory | the patterns (master and child, config-driven, gates, naming) apply to any orchestration tool; the syntax is ADF's |
| `BRONZE_Snowflake_Blob_Methodology.md` | Nogamy's bronze and landing methodology, written for Snowflake and Blob storage | the principles (source as is, ETL columns, idempotent windows) apply anywhere; stages and file formats are Snowflake's |

How they are used:
- The skills in `skills/` carry the method in short. The index and this project's deviations are in the `nogamy-method` skill.
- `base_prompt.md` is long. An AI never reads it whole: it finds the heading of the section it needs and reads that range.
- A project never patches a standard locally. A deviation is written in the deviations table of `nogamy-method`, with its reason and who decided.

To change a standard: change it in the starter, then bring the new version into the projects that want it.
