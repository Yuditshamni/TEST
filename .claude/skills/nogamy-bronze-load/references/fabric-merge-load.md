# Merge load — Microsoft Fabric

Part of `nogamy-bronze-load`. Read when `_context/platform.md` §2 names Fabric. The rules are in `merge-load.md`; this file adds what is true on the Fabric Warehouse (verified in a DEV workspace).

## Syntax

- `MERGE` from `PRE_BRONZE.PRE_<bronze table>` into `BRONZE.<bronze table>`; column lists generated from `sys.columns`.
- Keys match with `IS NOT DISTINCT FROM`; a changed column is found with `IS DISTINCT FROM`.
- `DELTA` window in an Oracle `SOURCE_QUERY`: `WHERE <change column> >= TO_DATE('__V_FROM_DATE__', 'YYYY-MM-DD HH24:MI:SS')` (the pipeline replaces the placeholder).
- Guard stop = `THROW`: the activity fails.

## No explicit transaction around flag + merge

Flagging is safe to repeat, the `MERGE` is atomic, and a transaction around both invites a write conflict with compaction (Fabric detects write conflicts per table). The pipeline activity that runs `BRONZE.SP_LOAD_BRONZE_<SYSTEM>` has `retry: 2`, `retryIntervalInSeconds: 30` for that reason (`nogamy-build-pipeline` → `references/fabric.md`). The window update (`Update_Config_Window`) resets `IS_MASS_DELETE_APPROVED`.

## Cost

Measured once on a few dozen tables: the full master run took about 1 minute longer with `MERGE` than with truncate. Measure on the project before relying on it.

## Testing on DEV

- A migration can be tried inside `BEGIN TRANSACTION` ... `ROLLBACK`, on a stable connection only: a dropped client left the session open with its locks, and catalog queries hung until `KILL` (find it: `sys.dm_exec_sessions`, `open_transaction_count > 0`).
- One query cannot mix `sys.*` and user tables.
