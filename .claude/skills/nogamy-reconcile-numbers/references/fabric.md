# nogamy-reconcile-numbers — Microsoft Fabric

Read when `_context/platform.md` §2 names Fabric.

## 2. Reconcile at three levels — running the queries

- DWH side: `python tools/fabric/wh_sql.py <server> WH_DWH "SELECT ..."`, or `@<file>.sql` for a whole file. Server: the DEV SQL endpoint (`PROJECT.md` → Environments).
- The command runs as the AI identity, in the DEV workspace only. Numbers from TEST or PROD come from a person.
- Aggregates only (`COUNT`, `SUM`, grouped by month or one dimension). The command prints every row it gets back, so never a query that returns rows of people or customers.
