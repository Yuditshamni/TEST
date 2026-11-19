# fabric/ — Fabric items, in Fabric's own format

What is published to the DEV workspaces (`PROJECT.md` → Environments). One folder per workspace, same layout as the workspace. The format is the one Fabric Git integration writes, so the folder works with or without it (the architecture document, `PROJECT.md` → Documents, §1.4–1.6).

```
fabric/
  data/                         -> the DEV workspace
    WH_DWH.Warehouse/           SQL project: one file per object, CREATE only
      WH_DWH.sqlproj
      <schema>/Tables/<object>.sql
      <schema>/Views/<object>.sql
      <schema>/StoredProcedures/<object>.sql
      <schema>/Functions/<object>.sql
    pipelines/_shared/          shared by all projects: Variable library, data-quality pipeline (GPL_DQA)
    pipelines/<project>/<NN_layer>/<name>.DataPipeline/pipeline-content.json   one folder per project; pipelines only
  bi/                           -> the BI DEV workspace
    <project>/<name>.SemanticModel/   TMDL
    <project>/<name>.Report/          PBIR
```

## Rules

- Same names in every environment: no `dev` / `prod` in any name, no environment in code, two-part references (`schema.object`). We deploy the same definitions everywhere.
- One object, one file: the current state. To change an object, edit its file **and** add a numbered migration in `scripts/migrations/` (`scripts/README.md`).
- Names: `nogamy-naming` skill (single source). Work tables: `#temp` only, never a permanent table.
- Pipelines: no hard-coded workspace, warehouse or SQL endpoint IDs. Read them from the Variable library.
- What Fabric does not deploy (grants, config rows, data moves) goes to `scripts/`.
- Published to DEV by the agent (`nogamy-dev-workflow` skill). Promoted to TEST and PROD by the GitHub Actions runner: TEST automatic after CI, PROD after a deliberate click (`nogamy-deploy` skill).

Owner: data engineer (`data/`), Power BI developer (`bi/`).
