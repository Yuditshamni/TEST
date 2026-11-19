# nogamy-git-workflow — Azure Data Factory

Read when `_context/platform.md` §2 names Azure Data Factory (or Synapse pipelines, where noted). Answers the "Platform specifics" topics of `SKILL.md` that the platform decides; the rest is per project in `_context/platform.md` §4.

## ADF Git mode

| Part | What it is |
|---|---|
| Providers | Azure DevOps Git (also Azure DevOps Server 2022), GitHub, GitHub Enterprise Cloud and Server. Not Bitbucket |
| Collaboration branch | the branch Studio publishes from; default `main`. Only this branch can be published |
| Feature branches | created in Studio or in Git; merged by a PR into the collaboration branch |
| Publish branch | ARM templates written by a Studio Publish; default `adf_publish`; renamed by `publish_config.json`. Only one at a time |
| Root folder | the repo folder that holds the factory's JSON (here `etl/adf/`, `nogamy-build-pipeline`) |
| One repo, factories | Azure Repos: a repository serves one factory. GitHub: several factories, each on its own branch |
| Which factory | only DEV is connected. TEST and PROD are never connected to Git (`nogamy-deploy`) |

## How it maps to our flow

- A topic branch per task (`nogamy-naming`). Studio users pick it in the branch list; the AI writes the JSON files on it.
- A PR into the collaboration branch, reviewed by a person. Direct commits to it are blocked by branch policy (Microsoft recommends it).
- Publish (or the automated export) runs from the collaboration branch after the merge. Who: `_context/platform.md` §5.
- `adf_publish` is generated output: never edit it, never base work on it, never merge it into `main`.

## Platform specifics — answers

| Topic | Azure Data Factory |
|---|---|
| Platform ↔ Git sync: exists? which direction? | yes, Studio ↔ the branch it has open (both ways). Studio cannot save to live DEV in Git mode |
| Tool → file | Studio saves each item as its own JSON on the open branch. Changes made by PowerShell, SDK or CLI go to live and are **not** entered into Git |
| File → tool | Studio reads the branch; live DEV gets it by Publish from the collaboration branch, or by an ARM deployment, or (AI in DEV) by the CLI (`nogamy-dev-workflow`) |
| Text formats in the repo | ADF JSON per item under the root folder; ARM templates only in the publish branch or the build artifact |
| Not in Git, and where it is recorded | secrets (Key Vault); a linked service with a secret, created in Studio (published to live at once); self-hosted IR machines and keys; trigger state (started or stopped). Record them in `_context/platform.md` §4 |

## Known traps

- Stale publish branch: an item changed by SDK/CLI, or a non-Key-Vault linked service deleted on an unmerged branch. Fix: "Overwrite live mode" (collaboration branch → live), or disconnect and re-import (live → branch).
- A non-Key-Vault linked service is published to live as soon as it is saved in Studio, from any branch.
- Linked services are not created by an import into a new branch: create them by hand.
- Files added by hand inside the root folder can break the factory loading. Keep READMEs and tools outside it.
- Signed commits are not supported by the integration.
- GitHub organization: an organization admin authorizes the `AzureDataFactory` app once.
- Synapse: Synapse Studio has its own Git integration; only the DEV workspace is connected; publish branch `workspace_publish` (`nogamy-deploy` → `references/adf.md`). verify: the rest of its Git model against the Synapse source-control page.

## Sources

- https://learn.microsoft.com/en-us/azure/data-factory/source-control
- https://learn.microsoft.com/en-us/azure/data-factory/continuous-integration-delivery
- https://learn.microsoft.com/en-us/azure/synapse-analytics/cicd/continuous-integration-delivery
