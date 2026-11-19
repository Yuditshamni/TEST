# Oracle through the gateway — Microsoft Fabric

Part of `nogamy-bronze-load`. Read when `_context/platform.md` §2 names Fabric and a source is Oracle reached through the on-premises data gateway. Generic Oracle rules first: `oracle-source.md`.

## How it lands (verified in a DEV workspace)

The Copy activity lands the data in parquet staging, then the warehouse `COPY` checks every column type strictly. What breaks:

| Symptom (`DWCopyCommandOperationFailed`) | Cause | Fix |
|---|---|---|
| `Cannot load managed ODP.NET driver` | OCMT 64-bit missing on the gateway machine. Creating the connection works without it (built-in driver), the pipeline does not | install OCMT, Default setup, restart the gateway service |
| `External data type 'DECIMAL(256, 130)' is currently not supported` | Oracle `NUMBER` without precision (also `COUNT(*)`) | in `SOURCE_QUERY`: `TO_CHAR(col)` or `CAST(col AS NUMBER(p,s))`, matching the bronze column |
| `Column 'X' of type 'DECIMAL(15, 0)' is not compatible with ... Parquet physical type: INT64` | Oracle `NUMBER(p,0)` with a small precision arrives as an integer, not a decimal | the bronze column is `BIGINT` (seen on `NUMBER(15,0)`) |
| `Column 'X' of type 'INT'/'DATETIME2' is not compatible with ... UTF8` | the value arrives as a string: a Copy `additionalColumns` value (always a string), or an Oracle `CHAR` column | ETL columns go in the Oracle query (`oracle-source.md`), never in `additionalColumns`; cast the source column in `SOURCE_QUERY` |

`typeConversion` in the Copy translator does not fix any of the above.

## Type mapping into the Fabric Warehouse (verified on a few dozen tables)

| Oracle | Bronze column | `SOURCE_QUERY` |
|---|---|---|
| `VARCHAR2(n)`, `CHAR(n)` | `VARCHAR(2n)`, up to 8000 | as is |
| `DATE` | `DATETIME2(0)` | as is |
| `NUMBER(p,0)`, `p` up to 9 | `INT` | as is |
| `NUMBER(p,0)`, `p` from 10 to 18 | `BIGINT` | as is |
| `NUMBER` without precision | `VARCHAR(50)` | `TO_CHAR(col) AS col` |

## Checking the real types

Run `PL_<Source>_To_Bronze` alone into a `BRONZE.TRY_` table with sink `tableOption: autoCreate`, read `sys.columns`, drop the table after.

## Pipeline traps

- A pipeline whose activity failed can still end `Completed` when the next activity depends on `Completed`. Check the activity runs, not only the pipeline status (`run_pipeline.py` prints them).
- Saving a pipeline that uses the Oracle connection needs a user the connection is shared with: `publish_pipeline.py --as-user`. Running it works as the AI identity.
