# nogamy-troubleshoot — Microsoft Fabric

Read when `_context/platform.md` §2 names Microsoft Fabric.

## 1. Get the facts

- Pipeline: status and `failureReason`: `python tools/fabric/run_pipeline.py <DEV workspace> <pipeline>` prints them. In the portal: Monitor → the run → the failed activity's output.
- Procedure: run it alone with `python tools/fabric/wh_sql.py <server> WH_DWH "EXEC <schema>.<procedure> ..."` and the same parameters.
- An environment differs: `python tools/migrate/run_migrations.py <endpoint> --dry-run` lists what is pending.
- Error text: search it in Microsoft Learn (MCP, `nogamy-platform-watch` → `references/fabric.md`) before guessing.

## 2. Known causes on Fabric

| Symptom | Usual cause | Fix |
|---|---|---|
| `Invalid object name` | wrong schema, wrong case, a three-part name | exact case, `schema.object` |
| pipeline in TEST reads DEV data | IDs typed into the pipeline JSON | the Variable library |
| `403` / `InsufficientPrivileges` for the agent | the identity is not in the workspace | add it to the DEV workspace only, Contributor |
| `refusing: not on the allow list` | the `tools/fabric` guard | intended; never add TEST or PROD |
| `invalid client secret` | the Secret ID saved instead of the Value, or expired | a new secret; store the Value |
| login popup `HTTP 404 adfs` in VS Code | the Windows sign-in broker | VPN, or `msal-no-broker` |
| Deploy button greyed (Fabric portal) | no items selected, or no Contributor on the source or target workspace | select items; check roles |
| `Failed to get Workspace Identity access token` | a `WorkspaceIdentity` connection on a workspace that has no identity yet | a workspace admin (not the AI) creates the identity and gives it a role in the workspace (`nogamy-build-pipeline`) |
| `Job failed to start: unable to acquire user token` right after the identity got its role | the role is not in effect yet | wait and re-run (passed about 35 minutes later) |
| child pipelines do not run after the first promotion | no Variable library value active in the workspace, no workspace identity, or no `FabricDataPipelines` connection | `nogamy-deploy` → `references/fabric.md` |
| Direct Lake model shows DEV data after a deploy | no rebinding | a data source rule |
| a Direct Lake model is slow, or queries DirectQuery | a view in the model: it falls back to DirectQuery | gold tables only (`nogamy-semantic-model`) |
