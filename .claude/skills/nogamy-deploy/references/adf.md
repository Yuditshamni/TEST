# nogamy-deploy — Azure Data Factory

Read when `_context/platform.md` §2 names Azure Data Factory (or Synapse pipelines, where noted).

## The path Microsoft recommends

- Only the DEV factory is connected to Git. TEST and PROD are not; they change only by an ARM template deployment from CI/CD.
- Every factory has the same item names. What differs is set by ARM template parameters at deployment.
- The AI prepares and checks. A person merges, and the CI/CD run (or a person) deploys. The AI never deploys to TEST or PROD.

## Two ways to build the ARM template (the project picks one, `_context/platform.md` §5)

| | Classic: `adf_publish` | Automated publish (npm) |
|---|---|---|
| Who builds it | a person clicks Publish in DEV Studio, on the collaboration branch only | a build pipeline on merge to the collaboration branch |
| Output | ARM templates in the publish branch (`adf_publish` by default; `publish_config.json` can rename it) | a build artifact; the live DEV factory is not changed by it |
| Command | none | `npm run build validate <rootFolder> <factoryId>` then `npm run build export <rootFolder> <factoryId> "ArmTemplate"` |
| Needs | Studio | `package.json` with `@microsoft/azure-data-factory-utilities`, Node.js 20.x |

- `factoryId` = `/subscriptions/<sub>/resourceGroups/<rg>/providers/Microsoft.DataFactory/factories/<DEV factory>`.
- Automated publish → turn on "disable publish" in the Git settings, so a Studio click does not overwrite it.
- No partial publish and no cherry-pick: a deployment carries the whole factory.

## The release, per target factory

1. Pre-deployment script: `PrePostDeploymentScript.ps1 -armTemplate <ARMTemplateForFactory.json> -ResourceGroupName <rg> -DataFactoryName <factory> -predeployment $true -deleteDeployment $false`: stops the triggers. The npm export ships the script; Microsoft's `PrePostDeploymentScript.Ver2.ps1` (Azure-DataFactory GitHub samples) stops only the changed ones.
2. ARM deployment of `ARMTemplateForFactory.json`, mode Incremental, with the parameter overrides of that environment.
3. Post-deployment script: the same with `-predeployment $false -deleteDeployment $true`: starts the triggers and **deletes the items removed from the template**.

- The script runs in PowerShell Core (`AzurePowerShell@5`, `pwsh: true`), latest Az module.
- Step 3 deletes items. List every removed pipeline, dataset, linked service or trigger in the deployment note.
- verify: the name of the parameters file the export writes (`ARMTemplateParametersForFactory.json`).

## Per-environment values

| What | How |
|---|---|
| server, database, URL in a linked service | ARM parameters (parameterized by default); a value per environment in the release's overrides |
| secrets | one Key Vault per environment, the **same secret names** in each: only the vault URL is a parameter |
| global parameters | "Include global parameters in ARM template" (Manage → ARM template, Git mode only); a value per environment in the overrides |
| anything else | `arm-template-parameters-definition.json` in the ADF root folder (syntax `<action>:<name>:<type>`, `=` keep default, `-` no default, `\|` Key Vault secret) |
| integration runtimes | the same name and type in every factory; a shared self-hosted IR through a linked IR |

- An ARM template holds at most 256 parameters. Custom parameters do not raise that limit.
- `encryptedCredential` does not move between factories: use Key Vault or a managed identity.

## Platform specifics — answers

| Topic | DEV → TEST | TEST → PROD |
|---|---|---|
| Mechanism | CI/CD: ARM deployment (Azure Pipelines or GitHub Actions) | same |
| Trigger, and who | per project: after merge, or a person starts the release | a deliberate approval by a person (`PROJECT.md` → People and roles) |
| How migrations are applied | `tools/run_migrations.py` on the target database, before the ARM deployment | same |
| How ETL items move | the ARM template of the whole factory, with the pre/post script | same |
| How the BI model and reports move | not ADF: the BI tool's own path (`nogamy-semantic-model`) | same |
| Per-environment values | ARM parameter overrides per environment; Key Vault per environment | same |
| What the mechanism does not move | data; Key Vault secrets; self-hosted IR machines and their keys; Git settings | same |
| Backup before a risky change; rollback | the previous ARM artifact (or `adf_publish` commit), deployed again; database backup is the database's | same |
| Release window, outside approvals | per project (`_context/platform.md` §5) | per project |

## Known traps

- A trigger left running during the deployment: the pre-deployment script is missing or failed.
- Items deleted in the target: the post-deployment script removes what the template no longer has.
- IR name or type differs between factories: the deployment fails or runs on the wrong runtime.
- Deploying the factory ARM template to the DEV factory resets its `lastCommitId`: every item then shows as new on the next publish.
- Synapse: artifacts are not ARM resources. Use the "Synapse workspace deployment" task (operations validate, deploy, validateDeploy); publish branch `workspace_publish`; templates `TemplateForWorkspace.json` + `TemplateParametersForWorkspace.json`; custom parameters `template-parameters-definition.json`; its trigger toggle stops triggers; self-hosted IRs are created by hand in each workspace.

## Sources

- https://learn.microsoft.com/en-us/azure/data-factory/continuous-integration-delivery
- https://learn.microsoft.com/en-us/azure/data-factory/continuous-integration-delivery-improvements
- https://learn.microsoft.com/en-us/azure/data-factory/continuous-integration-delivery-sample-script
- https://learn.microsoft.com/en-us/azure/data-factory/continuous-integration-delivery-resource-manager-custom-parameters
- https://learn.microsoft.com/en-us/azure/data-factory/author-global-parameters
- https://learn.microsoft.com/en-us/azure/data-factory/source-control
- https://learn.microsoft.com/en-us/azure/data-factory/concepts-integration-runtime
- https://learn.microsoft.com/en-us/azure/synapse-analytics/cicd/continuous-integration-delivery
