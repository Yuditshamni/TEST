# nogamy-explore-data — Microsoft Fabric

Read when `_context/platform.md` §2 names Fabric. The rules in `SKILL.md` are the same; this file says how to run the profile on the Fabric Warehouse.

Needs the Fabric pack (`tools/fabric/`, `PROJECT.md` → `Packs: fabric`). Missing → run `nogamy-add-pack` first.

- Run in the DEV warehouse only, as the AI identity: `python tools/fabric/wh_sql.py <server> WH_DWH "<query>"` (or `@<file>.sql`). The command is also listed in `PROJECT.md` → Agent tools.
- Sources outside Fabric: through the profile query the developer runs there, or through the bronze copy.
- T-SQL: `LEN(col)` instead of `LENGTH(col)`; never `SELECT TOP (n) *` on a table with sensitive columns.
- Structure: `INFORMATION_SCHEMA.COLUMNS` or `sys.columns` (one query cannot mix `sys.*` and user tables).
- Fabric is case sensitive: mixed case in codes splits a value in two (`'A' <> 'a'`). Flag it with the count of each spelling.
