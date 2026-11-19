# Try-outs and DEV cleanup

Part of `nogamy-db-objects` ("Anything not final"). Open when the work is a test, a demo or a try-out, or when the repo-vs-DEV check lists leftovers. Platform syntax and commands: `fabric.md` (or the project's platform reference).

## `TRY_` objects

- Shared framework objects (`MNG`, the quality framework) keep their real names. Only the try-out's own objects get `TRY_`: bronze, views, staging, gold, procedure, its config and quality-check rows.
- **`TRY_` never reaches the main branch.** It lives on a branch, with object files and a migration like any change.
  - Approved → rewrite the branch's migration with the final names and run it again in DEV. The `TRY_` objects and rows become DEV cleanup (below).
  - Dropped → DEV cleanup.

## Temp tables

Session scoped only: gone when the session ends. Use them for anything that does not have to outlive the session. Syntax and form: the platform reference.

## DEV cleanup

- The repo-vs-DEV check (a drift check tool, or a catalog query listed in `tools/README.md`) lists objects in DEV without a file. A listed work table: report it. **The developer** drops it before the PR. The AI never deletes.
- Same for anything a branch built in DEV and then changed its mind about (an old view, a dropped column, a `TRY_` object). It never reached the main branch, so it is **not** a migration. The developer cleans it in DEV by hand; the PR description lists it under "DEV cleanup before merge" (`scripts/README.md`).
