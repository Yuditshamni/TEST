# Merge load

Part of `nogamy-bronze-load`. Open when building or debugging a `FULL_MERGE` / `DELTA` load, the mass-delete guard, or a new `PRE_BRONZE` table. Platform syntax and what was verified on it: `fabric-merge-load.md` (or the project's platform reference).

## Modes

Bronze keeps a row untouched unless a column changed, so gold receives only changes, and a failed extract does not empty bronze.

| Mode | `PRE_BRONZE` holds | Source deletes |
|---|---|---|
| `FULL_MERGE` | the whole source table | soft delete (`DELETED_DATE`) |
| `DELTA` | one window: the source query filters `<change column> >= <from date of the window>` | not detected |
| `FULL` | not used: truncate and reload | gone with the truncate |

`FULL` is only for a table with no key yet (an open question): no merge, no guard, no soft delete.

## Steps

The extract lands in `PRE_BRONZE.PRE_<bronze table>`, truncated first. `Duplicates` runs on it: the merge needs one source row per key. Then `BRONZE.SP_LOAD_BRONZE_<SYSTEM>`:

1. guard, `FULL_MERGE` only (below)
2. flag what gold confirmed (`IS_LAST_INSERT_TO_BRONZE_IND = 0`, `nogamy-bronze-load` → Watermark)
3. merge, column lists read from the catalog (not typed by hand):
   - new key: insert
   - same key and any column changed (NULL-safe compare, without the keys and the ETL columns), or the row was soft deleted: update, new `LOAD_TO_BRONZE_TS`, flag `1`, `DELETED_DATE = NULL`; `ETL_INSERT_DATE` is kept
   - same key, nothing changed: untouched, so it does not reach gold again
   - `FULL_MERGE` only, key missing from the source: `DELETED_DATE`, new `LOAD_TO_BRONZE_TS`, flag `1`, so gold sees it

## Rules

- Keys match NULL-safely (`IS NOT DISTINCT FROM` or the dialect's equivalent): with `=`, a NULL in a key would insert the row and soft delete the old one on every run.
- No hash column: the comparison is generated, needs no backfill, no NULL marker, no date format. Reading all columns is cheap at normal sizes. Measure before changing that.
- Key only is not enough: it finds new and deleted rows, not a changed row.
- Never delete in the merge, and never a "not matched by source" branch on a window: a window is a partial batch.
- A changing column in the key (an end date, an update date, a description) shows as a soft delete plus a new row: fix the key.
- Gold reads `DELETED_DATE`. A full-reload gold table with no watermark row still works: the flag stays `1`, so filter or mark deleted rows.
- Cost: a merge is slower than a truncate and reload. Measure on the project before relying on a number.

## Mass-delete guard (`FULL_MERGE`, before any write)

`ACTIVE` = bronze rows with `DELETED_DATE IS NULL`; `MISSING` = active rows whose key is not in `PRE_BRONZE`.

- `PRE_BRONZE` empty and `ACTIVE > 0`: stop. Approval does not release it.
- `MISSING` above a count **and** above a share of `ACTIVE` (default: `> 10` and `> 5%`; the project may set its own in `_context/platform.md` §10): stop, unless `IS_MASS_DELETE_APPROVED = 1`.
- Stop = the procedure raises an error, the step fails, bronze is unchanged, the window does not advance. Find out why. A real mass delete: a person sets the flag, runs again; the window update after a successful run resets it.
- A partial extract under the threshold passes; the next good run clears `DELETED_DATE`.

## A new merge table

- A `PRE_BRONZE` table with the bronze columns, without `DELETED_DATE`, plus the config row.
- `DELTA` only with a filled change column outside the key that also moves on retroactive changes; prove it against a `FULL` copy compared by key. A gap: back to `FULL_MERGE`.
