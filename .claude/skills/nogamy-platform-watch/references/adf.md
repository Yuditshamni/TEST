# nogamy-platform-watch — Azure Data Factory

Read when `_context/platform.md` §2 names Azure Data Factory (or Synapse pipelines).

## Source

Microsoft Learn only (the `microsoft-learn` MCP server when the project has it; else the pages by web access, or "not verified").
Start of each daily check: "What's new in Azure Data Factory"; then each watch-list item.

## Watch list topics

| Topic | Why we watch it |
|---|---|
| Git integration: collaboration and publish branches, the folder layout under the root folder | the repo layout under `etl/adf/` and the drift check (`nogamy-git-workflow`, `nogamy-dev-workflow`) |
| Automated publish (`@microsoft/azure-data-factory-utilities`), ARM template limits, parameterization template | promotion between environments (`nogamy-deploy`) |
| Global parameters and linked-service parameters, Key Vault references | per-environment values; no environment inside an item (`nogamy-build-pipeline`) |
| Activities: Copy, Lookup, ForEach (batch count, nesting), Execute Pipeline, Script, Stored Procedure; retry policy | the master/child pattern and the gates (`nogamy-build-pipeline`, `nogamy-bronze-load`) |
| Self-hosted integration runtime: versions, auto-update, supported sources | on-prem sources (`nogamy-bronze-load`) |
| `az datafactory` CLI and REST API: create-run, run status, activity runs | how the AI runs and reads a pipeline in DEV (`nogamy-dev-workflow`) |
| Product direction: Data Factory in Microsoft Fabric vs Azure Data Factory | a client choosing between them; the move path |
