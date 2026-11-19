# nogamy-troubleshoot — Azure Data Factory

Read when `_context/platform.md` §2 names Azure Data Factory (or Synapse pipelines, where noted).

## 1. Get the facts

- Pipeline: `az datafactory pipeline-run show … --run-id <runId>` (status, message), then `az datafactory activity-run query-by-pipeline-run …` for **every activity**: `status`, `error.errorCode`, `error.message`, `output` (`nogamy-dev-workflow` → `references/adf.md`). In Studio: Monitor → the run → each activity's input, output, error.
- A child pipeline has its own run: read its activities too.
- Copy: the output has `rowsRead`, `rowsCopied`, `rowsSkipped`, `copyDuration`, `effectiveIntegrationRuntime`, `errors`; Studio's Details view shows the slow stage.
- Procedure: run it alone in the database with the same parameters (`nogamy-write-sql`).
- Older than 45 days: the run is gone from ADF (only Azure Monitor diagnostics, if set up).
- Error text: search it in the ADF troubleshooting guides on Learn before guessing.

## 2. Known causes on ADF

| Symptom | Usual cause | Fix |
|---|---|---|
| ForEach skipped tables, no error | the Lookup returned only its first 5,000 rows | fewer rows per Lookup: split by group, two-level pipeline |
| Lookup fails on a procedure | it returned no result set, or more than one | return exactly one result set |
| `2001` output length over limit | an activity output over about 4 MB | return less (counts, not rows) |
| `2002` payload too large | activity + dataset + linked service config over 896 KB | smaller expressions; move lists to config |
| `2003` throttling | too many concurrent external activities | lower `batchCount`; spread schedules |
| `2010` self-hosted IR is offline | the node service stopped, or no outbound 443 | a person checks the node; Microsoft's IR troubleshooting guide |
| `2108` error calling the endpoint | URL, DNS, certificate, network, or a localhost URL on the Azure IR | fix the URL; localhost only through a self-hosted IR |
| `2103` / `2104` / `2105` property missing or wrong type | a parameter not passed, or an expression of the wrong type | match caller and callee parameters (`nogamy-build-pipeline`) |
| a child gets a string where an array was sent | `ExecutePipeline` passes arrays as strings | verify: the fix in the troubleshoot guide |
| iterations overwrite each other's values | `SetVariable` inside a parallel ForEach | move the logic into the child pipeline |
| `UserErrorJreNotFound` on a self-hosted IR | no Java runtime for Parquet / ORC / Avro | a person installs JRE 11+ and sets `JAVA_HOME` |
| a pipeline in TEST reads DEV data | a server, URL or database typed into a linked service, or not overridden at deployment | ARM parameter overrides / Key Vault per environment (`nogamy-deploy`) |
| pipeline works in DEV, fails after deploy | IR name or type differs, or `encryptedCredential` in a linked service | same IR name and type; Key Vault or managed identity |
| a fix made in DEV disappeared | it was made by CLI/SDK (not in Git) and a publish overwrote it | put the fix in the repo file |
| publish shows stale or missing items | stale publish branch | "Overwrite live mode" (a person), then publish |
| every item shows as new on publish | the factory ARM template was redeployed to DEV (`lastCommitId` reset) | publish again; do not redeploy the factory ARM to DEV |
| ARM deployment refused: too many parameters | over 256 template parameters | trim `arm-template-parameters-definition.json`; global parameters |
| a trigger ran during a deployment | the pre-deployment script did not run | add or fix the pre/post script (`nogamy-deploy`) |
| items vanished in TEST after a deploy | the post-deployment script deletes what the template no longer has | intended; list removals in the deployment note |
| `403` / authorization failed for the AI | no Data Factory Contributor on the DEV factory | a person grants it on DEV only; outside DEV is intended |

## Sources

- https://learn.microsoft.com/en-us/azure/data-factory/data-factory-troubleshoot-guide
- https://learn.microsoft.com/en-us/azure/data-factory/self-hosted-integration-runtime-troubleshoot-guide
- https://learn.microsoft.com/en-us/azure/data-factory/copy-activity-monitoring
- https://learn.microsoft.com/en-us/azure/data-factory/monitor-programmatically
- https://learn.microsoft.com/en-us/azure/data-factory/control-flow-lookup-activity
- https://learn.microsoft.com/en-us/azure/data-factory/control-flow-for-each-activity
- https://learn.microsoft.com/en-us/azure/data-factory/source-control
- https://learn.microsoft.com/en-us/azure/data-factory/continuous-integration-delivery-resource-manager-custom-parameters
