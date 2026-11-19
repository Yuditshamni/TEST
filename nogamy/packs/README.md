# nogamy/packs/ — platform packs

A pack = the files only one platform needs. The template root holds none of them.

- `<name>.txt` — the list of the pack's files, at their **project** path (syntax: `nogamy/core-manifest.txt`).
- `<name>/` — the core's stored copy of those files, at the same project path
  (`fabric/tools/fabric/wh_sql.py` here → `tools/fabric/wh_sql.py` in a project).

A project gets a pack's files only when it adds the pack (`nogamy-add-pack`, PROJECT.md → `Packs:`).
The stored copies never stay in a project: the first core update removes `nogamy/packs/*/` (`nogamy/core-only.txt`).
Change a pack here, in the core repo; `python nogamy/ops/validate_core.py` checks that every listed file is stored and
that no pack file sits at the template root.

| Pack | For | Files |
|---|---|---|
| `fabric` | Microsoft Fabric | `fabric/` framework objects (MNG, QA, `SP_DQA`, `GPL_DQA`), `tools/fabric/`, `tools/migrate/`, Microsoft Learn MCP (`.mcp.json`, `.vscode/mcp.json`) |