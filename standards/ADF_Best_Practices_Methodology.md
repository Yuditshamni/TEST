<!-- converted to Markdown from ADF_Best_Practices_Methodology.docx on 2026-10-20; original kept outside the repo -->

**ADF Pipeline Design**

**Best Practices & Methodology**

A guide to designing maintainable, scalable, and config-driven Azure Data Factory pipelines

## 1. Pipeline Naming Conventions

Consistent naming is the foundation of a maintainable ADF project. A pipeline name should communicate three things at a glance: what it does, which domain or data group it belongs to, and which layer it operates on. Adopt a convention at the start of the project and enforce it without exceptions.

### 1.1 General Pattern

PL_<Action>_<Domain>_<Layer>

The PL_ prefix identifies a pipeline (as opposed to a dataset, linked service, or trigger). <Action> describes what the pipeline does, <Domain> is the data domain or source system, and <Layer> is the architecture layer it targets.

**Example:** PL_Run_Electricity_Bronze — runs the full Bronze ingestion for the Electricity domain.PL_Date_Range_Params_Master — Master pipeline for the Date_Range_Params API group.PL_Meteo_Date_Range_Params_To_BRONZE — loads Meteo date-range files from Blob into Bronze.

**Note:** The examples above are from a specific project. Adapt the domain names and layer labels to your own project. What matters is consistency: pick a convention and apply it everywhere.

### 1.2 Pipeline Suffixes

The suffix communicates the pipeline's role in the data flow. The table below lists suffixes used in one reference implementation. Adapt them to your project — the important thing is that every role has a dedicated, consistent suffix that the whole team recognises.

| **Suffix** | **Role** | **Example** |
|---|---|---|
| _Master | Entry point for a group. Reads config, drives the loop. | PL_Date_Range_Params_Master |
| _To_BRONZE | Loads source data through PRE_BRONZE into BRONZE. Runs DQA. Updates config. | PL_Meteo_Date_Range_Params_To_BRONZE |
| _Daily_Run | Scheduled orchestration trigger. | PL_Solar_Daily_Run |
| PL_Run_<Domain>_Bronze | Domain-level Bronze orchestration wrapper. | PL_Run_Gas_Bronze |
| PL_Run_<Domain>_Gold | Domain Silver → Gold orchestration. | PL_Run_Electricity_Gold |

**Note:** These suffixes are examples, not a universal standard. Every project will have its own data flows and may need different or additional suffixes. Define yours at the start and document them here.

When Azure Blob Storage is used as an intermediate landing zone before Bronze ingestion, additional suffixes are common for the Blob-related steps. These are project-specific and depend on the architecture; they are not part of a universal standard.

**Example:** _To_Blob — calls the source API and writes raw files to Blob Storage._To_Blob_Data_Prep — prepares or transforms data before the Blob write._To_Blob_Raw_Data — writes raw (untransformed) data to Blob._Blob_Pages_Loop — internal paging loop inside a Blob write step.These suffixes apply only when Blob Storage is part of the pipeline flow. If your architecture loads directly from source to Bronze, you do not need them.

### 1.3 Global / Reusable Pipelines

Pipelines that are shared across multiple domains use a different prefix — for example GPL_ (Global Pipeline). These should never contain domain-specific logic or hardcoded table names.

**Example:** GPL_DQA — atomic DQA executor, called by any domain.GPL_DQA_Group — group runner that reads DQA config from a table and calls GPL_DQA in a loop.

### 1.4 Activity Naming

Activities inside a pipeline follow the same spirit of self-documenting names:

- Script activities (SP calls): name matches the SP, e.g. SP_FACT_Sales, SP_Dim_Customer.

- ExecutePipeline activities: describe the action, e.g. "Source_To_Blob", "Blob_To_BRONZE", or "Execute DQA_Dims".

- Lookup activities: describe what is retrieved, e.g. "Get_Tables_Params_From_MNG_API_Configuration", "CK_For_SPECIAL_DATES".

- SetVariable activities: "Set_<variable_name>", e.g. "Set_V_Token", "Set_V_From_Date".

- Wait activities (sync barriers): name the completed stage, e.g. "Finish Dims not Related", "Finish Facts".

- Wait activities (visual separators in orchestration): "RUN <Domain>", e.g. "RUN Electricity", "RUN Gas".

### 1.5 Parameters and Variables

Use a consistent prefix convention to distinguish parameters from variables and to make their source obvious at a glance:

- Pipeline parameters: P_ prefix. These are passed in from outside, e.g. P_API_Group, P_Target_Table_Name.

- Pipeline variables: V_ prefix. These are computed at runtime inside the pipeline, e.g. V_Token, V_From_Date.

Always declare a defaultValue on parameters that have a sensible default. This allows the pipeline to be triggered manually in isolation (using the default) without requiring the caller to supply every parameter. It also serves as self-documentation.

**Example:** P_API_GROUP defaultValue: "Date_Range_Params" — so the Master can run standalone.

## 2. Folder Structure

Organise pipelines into a numbered folder hierarchy that mirrors the data flow. Numbering guarantees the folders sort in logical order in the ADF UI regardless of how many domains are added later.

1: Orchestration/

1.1: Schedule_Runs <- scheduled trigger entry points

1.2: <Domain A> <- domain-level run pipelines

1.3: <Domain B>

...

2: Implementation/

2.1: <Source System A>

2.1.1: <API Group 1> <- Master + To_Blob + To_BRONZE

2.1.2: <API Group 2>

2.2: <Source System B>

...

3: Utilities/ <- DQA and shared helpers

**Example:** 1: Orchestration/1.2: Electricity contains PL_Run_Electricity_Bronze and PL_Run_Electricity_Gold.2: Implementation/2.2: Meteo/2.2.3: Meteo_Date_Range_Params contains PL_Meteo_Date_Range_Params_Master, _To_Blob, _To_BRONZE.

### 2.1 Rules

- The Orchestration folder contains only wrappers and schedulers. No raw data logic goes here.

- One sub-folder per source system, then one per API group within it. Each API group folder holds exactly the pipelines for that group.

- Utilities holds shared DQA pipelines and any cross-cutting helpers — nothing domain-specific.

- Keep prefix numbers sparse (1.1, 1.2, 1.3 ...) so new domains can be inserted without renumbering everything.

## 3. Config-Driven Architecture: The Management Table

The most important principle in this design: no API-specific information is hardcoded inside a pipeline. Every attribute that varies between APIs — target table, entity, delta dates, primary keys, active flag — lives in a central management table. Pipelines read this table at runtime and pass values downstream as parameters. Adding a new source table requires only a new row in the table, no pipeline changes.

### 3.1 Key Columns

| **Column** | **Purpose** |
|---|---|
| API_GROUP | Groups related APIs. Used by Master as a filter (IS_ACTIVE=1 AND API_GROUP=<group>). |
| API_NAME | Unique identifier for a specific API or table. |
| SOURCE_SYSTEM | Source system name, e.g. "Meteo", "External", "natgaz". |
| ENTITY_NAME | Entity or site identifier, passed into child pipelines. |
| TARGET_TABLE_NAME | Snowflake target table name — passed as a parameter to To_BRONZE. |
| TARGET_TABLE_KEYS | Comma-separated primary keys — passed to DQA for duplicate checks. |
| EXTRACT_MODE | Load strategy: FULL, DELTA, Incoming_Files, etc. |
| LAST_TO_DAILY_DELTA | Last successfully processed date. Base for next run start date. |
| LAST_FROM_DAILY_DELTA | Start date of the last completed run (for audit). |
| IS_ACTIVE | 0 / 1 flag. Only rows with IS_ACTIVE=1 are processed. |
| LAST_INSERT_TO_BRONZE_DATETIME | Updated by ADF after each successful Bronze load. |

### 3.2 How Parameters Flow

The Master pipeline performs a Lookup against the management table filtered on IS_ACTIVE=1 and the current API_GROUP. The result set is iterated with a ForEach. For each row, the Master passes the row's columns as parameters to the child pipelines:

Management table row

-> Master (Lookup + ForEach)

-> To_Blob (P_API_Name, P_Entity, P_Token, LAST_TO_DAILY_DELTA, ...)

-> To_BRONZE (P_API_Name, P_Target_Table_Name, P_Target_Table_Keys, ...)

**Note:** Never hardcode a table name, schema name, or entity identifier inside a pipeline expression. If a value can differ between APIs, it belongs in the management table.

### 3.3 The IS_ACTIVE Flag

The IS_ACTIVE flag is the operational on/off switch for each API. Setting IS_ACTIVE=0 stops that API from being processed on the next run without touching any pipeline. This is the correct way to temporarily disable a source — never comment out activities or delete rows from the management table.

### 3.4 Updating the Table After Each Run

After a successful Bronze load, the To_BRONZE pipeline must update the management table: at minimum set LAST_INSERT_TO_BRONZE_DATETIME = GETDATE(). For incremental loads also update LAST_FROM_DAILY_DELTA and LAST_TO_DAILY_DELTA. This must happen after DQA passes — if DQA fails, the delta pointer must not advance.

## 4. The Master Pipeline Pattern

Every group of related APIs shares a single Master pipeline. The Master is the only pipeline that knows the management table exists. Child pipelines (To_Blob, To_BRONZE) are completely agnostic of it — they only see their input parameters. This separation means you can run any child pipeline in isolation for testing simply by supplying the parameters manually.

### 4.1 Core Structure

The Master always starts with a Lookup + ForEach. What runs inside the ForEach depends on the source type. Two common variants:

Variant A — ADF fetches data from a source API:

1. Lookup MNG_API_CONFIGURATION (IS_ACTIVE=1, API_GROUP=<group>)

2. ForEach over result rows:

a. Execute To_Blob (fetch from API -> write files to Blob)

b. Execute To_BRONZE (depends on To_Blob Succeeded)

Variant B — files already arrive in Blob independently:

1. Lookup MNG_API_CONFIGURATION (IS_ACTIVE=1, API_GROUP=<group>)

2. ForEach over result rows:

a. Execute To_BRONZE (reads files already in Blob)

**Note:** Variant A is an example, not the default. The deciding factor is whether ADF is responsible for extracting the data. If a vendor places files in Blob independently (SFTP drop, automated export, etc.), To_Blob does not exist for that source.

**Example:** PL_Meteo_Date_Range_Params_Master uses Variant A (ADF calls the Meteo API).PL_External_RoofTop_Master uses Variant B (files arrive in Blob from an external party).

### 4.2 ForEach Configuration

- Set isSequential: false and batchCount: 5 (or similar) to run up to 5 iterations in parallel. Adjust based on source API rate limits and Snowflake concurrency.

- Set firstRowOnly: false on the Lookup so the full result set is available as an array for ForEach to iterate.

- Set waitOnCompletion: true on every ExecutePipeline activity inside the ForEach. This ensures the child pipeline fully completes (including its own DQA and config update) before the loop moves on.

### 4.3 API Group Parameter

Declare P_API_GROUP on the Master with a defaultValue equal to the group name. This allows the pipeline to be triggered in isolation (using the default) or called from a parent orchestration that overrides the value. Both modes use the same pipeline — no duplication needed.

### 4.4 Authentication Tokens

When a source API requires a token, request it once at the start of the Master pipeline using a WebActivity, store the result in a pipeline variable (V_Token), and pass it to each child pipeline invocation via a parameter. Never request a new token inside the ForEach loop unless the token TTL requires it.

## 5. Incremental Loading and Delta Management

A well-designed incremental pipeline processes only new data on normal runs (delta), and also allows an operator to override the date range for backfills or reruns without modifying any pipeline code.

### 5.1 Normal Delta Flow

The start date of each run is derived from LAST_TO_DAILY_DELTA stored in the management table (minus one day, to ensure no gaps at boundaries). The end date is the current timestamp (utcNow()). Both values are resolved inside the To_BRONZE pipeline and stored in variables V_From_Date and V_To_Date before any SP is called.

V_From_Date = LAST_TO_DAILY_DELTA - 1 day

V_To_Date = utcNow()

### 5.2 Special Dates Override

A dedicated override table (e.g. MNG_API_SPECIAL_DATES_DELTA_RUN) allows operators to request a specific date range for a specific API on the next run. The To_BRONZE pipeline checks this table first via a Lookup. If an active override exists (IS_DONE=0), it uses the override dates instead of the standard delta logic. After the run completes, the pipeline sets IS_DONE=1.

| **Step** | **Activity** | **Logic** |
|---|---|---|
| 1 | CK_For_SPECIAL_DATES | Lookup from override table for this API. |
| 2 | If_Special_For_Date_Set | IS_DONE=0: V_From_Date and V_To_Date from override row. Else: standard delta. |
| 3 | Bronze load SPs | Execute load with V_From_Date / V_To_Date. |
| 4 | Update config | Set LAST_TO_DAILY_DELTA, LAST_FROM_DAILY_DELTA in management table. |
| 5 | If_Special_For_Update | If override was used: set IS_DONE=1 in override table. |

**Note:** The override table gives operations teams a controlled, auditable way to re-process historical date ranges without touching any pipeline code or creating ad-hoc manual triggers.

### 5.3 File-Level Deduplication

For file-based sources, maintain a file tracking log table (e.g. MNG_BLOB_FILES_LOG). Each file that lands in Blob gets a row. The To_BRONZE pipeline filters to only files where IS_INSERT_TO_BRONZE=0. After a successful load, the pipeline updates those rows to IS_INSERT_TO_BRONZE=1. This prevents double-processing if a pipeline reruns after a partial failure.

## 6. Two-Step Bronze Ingestion: PRE_BRONZE -> BRONZE

Raw data from Blob Storage is never loaded directly into the final BRONZE tables. It always passes through an intermediate PRE_BRONZE layer first. This two-step approach isolates raw parsing failures from the clean Bronze tables and makes partial reruns safe.

### 6.1 The Two Steps

Step 1 — Blob -> PRE_BRONZE

Read raw files (JSON / XML / CSV) from the Blob stage.

Load into a PRE_BRONZE_Raw_Data table (single ROW_DATA column).

Then parse into typed PRE_BRONZE columns.

SP: SP_LOAD_*_To_PRE_BRONZE_Row_Data(...)

Step 2 — PRE_BRONZE -> BRONZE

Flatten / transform the typed PRE_BRONZE data.

Load into the final BRONZE table with full column structure.

SP: SP_LOAD_*_TO_BRONZE(...)

### 6.2 Why Two Steps

- If parsing fails, only PRE_BRONZE is affected. BRONZE remains unchanged and the previous good load is safe.

- PRE_BRONZE can be inspected to debug malformed source files without touching BRONZE.

- Step 1 can be re-run independently without re-fetching files from the source API.

- Schema changes in the source affect only the parsing stored procedure, not the ADF pipeline JSON.

### 6.3 Generic Stored Procedures

Use generic, parameterised stored procedures rather than one SP per table. Pass the schema name, table name, and entity name as parameters at runtime. This means adding a new source table requires only a new row in the management table — not a new stored procedure and not a new pipeline.

**Example:** MNG.SP_LOAD_Full_Tables_To_BRONZE(schema, table_name) — used for any FULL-mode table.MNG.SP_LOAD_INC_TABLES_BY_SITE_AND_DATE_TIME_TO_BRONZE(table_suffix) — used for any incremental table identified by site + datetime.

## 7. Dynamic Expressions and Connections

ADF expressions use @concat() to build SQL strings dynamically at runtime. This is the mechanism that makes config-driven pipelines possible: the pipeline JSON contains no hardcoded table names or schema names — only expressions that resolve to the correct values from parameters or variables.

### 7.1 Building Dynamic SQL in Script Activities

Every Script activity that calls a stored procedure wraps the call in @concat(). Single quotes inside the SQL string are escaped by doubling them. Pipeline parameters are injected via pipeline().parameters.<name>; variables via variables('<name>').

"@concat(

'CALL BRONZE.SP_LOAD_INC_TABLES_BY_SITE_AND_DATE_TIME_TO_BRONZE(''',

pipeline().parameters.P_Target_Table_Name,

'')'

)"

**Example:** From PL_Meteo_Date_Range_Params_To_BRONZE:@concat('CALL DWH_DEV.MNG.SP_LOAD_INC_TABLES_BY_SITE_AND_DATE_TIME_TO_BRONZE(''', pipeline().parameters.P_Target_Table_Name, '_', pipeline().parameters.P_Source_System, ''')')

### 7.2 NonQuery vs Query Script Type

Script activities have two types for the scripts array:

- "Query" — for statements that return a result (SELECT, CALL SP that returns data). Use for SP calls that run a load.

- "NonQuery" — for statements that modify data but return nothing (UPDATE, INSERT). Use for management table updates and log flag updates.

**Note:** Using the wrong type does not always cause an error, but it signals intent incorrectly and can cause issues with certain connectors. Be explicit.

### 7.3 Generic Datasets

Instead of creating one dataset per table, create a single generic dataset that accepts schema name and table name as parameters. All pipelines that query Snowflake reference this one dataset, passing different parameter values at runtime. This keeps the dataset count low and eliminates the need to create a new dataset whenever a new table is added.

### 7.4 Blob File Path Convention

Standardise the Blob path structure so that SPLIT_PART positions in Snowflake stage queries are predictable across all source systems:

Raw_Data/<source_system>/<api_group>/<table_name>/<entity>/<year>/<month>/<day>/<file>

**Example:** Raw_Data/Meteo/Meteo_Date_Range_Params/Basics_Measurement/SiteA/2025/2025-06/2025-06-10/data.json

**Note:** Document the SPLIT_PART position for each source system. Different sources may have different path depths; keep this in a reference file alongside the pipeline JSONs.

## 8. Data Quality Assurance (DQA)

DQA is a first-class step in every pipeline. The pattern separates DQA configuration (which checks to run, on which tables) from DQA execution (always the same pipeline). Adding a new check requires only inserting a row in a config table — no pipeline changes.

### 8.1 Two-Level Architecture

| **Pipeline** | **Role** |
|---|---|
| GPL_DQA | Atomic executor. Receives DQA type, table name, keys, optional query. Runs one check, logs the result. |
| GPL_DQA_Group | Group runner. Receives a group name. Looks up all active DQA definitions for that group, calls GPL_DQA for each. |

DQA definitions live in a management table (e.g. MNG_DQA_QUERY). Each row has GROUP_NAME, DQA_TYPE (Duplicates, Empty_Table, Custom_Query, ...), TABLE_NAME, TABLE_KEYS, an optional custom DQA_QUERY, a THRESHOLD, and IS_ACTIVE.

### 8.2 When to Run DQA

- Bronze — after each To_BRONZE load. Check at minimum for duplicates and empty tables. Call GPL_DQA directly (table name comes from a parameter).

- Gold Dims — after all dimension SPs complete, before facts start. Call GPL_DQA_Group with group "<Domain>_GOLD_Dims".

- Gold Facts — after all fact SPs complete. Call GPL_DQA_Group with group "<Domain>_GOLD_Facts".

- SERVE / Others — optional, after Facts DQA: checks on the SERVE views, if the domain has them. Call GPL_DQA_Group with group "<Domain>_Others".

**Note:** DQA gates progress. Facts do not start until Dims DQA passes. The domain run does not succeed until Facts DQA passes. This prevents downstream layers from building on bad data.

## 9. Gold Orchestration

The Gold pipeline transforms Bronze data through Silver into Gold dimension and fact tables. SERVE is an optional layer of views on Gold — typically used to join several Gold tables or shape data for a report. Views are not loaded, so SERVE adds no step that loads data to the pipeline.

**Note:** SERVE is an architectural choice, not a requirement. By default the BI model reads Gold. Omit phase 7 below if a domain has no SERVE views.

### 9.1 Standard Run Order

Phase 1: Dims (all in parallel, dependsOn: [])

SP_Dim_A, SP_Dim_B, SP_Dim_C ...

Phase 2: Sync barrier (Wait 1s, depends on ALL dims)

"Finish Dims"

Phase 3: Dims DQA

GPL_DQA_Group (P_DQA_GROUP_NAME = "<Domain>_GOLD_Dims")

Phase 4: Facts (sequential or parallel per dependency chain)

All facts depend on Dims DQA Succeeded

Phase 5: Sync barrier (Wait 1s, depends on ALL facts)

"Finish Facts"

Phase 6: Facts DQA

GPL_DQA_Group (P_DQA_GROUP_NAME = "<Domain>_GOLD_Facts")

Phase 7 [optional]: SERVE / Others DQA

depends on Facts DQA Succeeded; checks on the SERVE views (no load step: views read Gold)

GPL_DQA_Group (P_DQA_GROUP_NAME = "<Domain>_Others")

### 9.2 The Role of Wait Activities

Wait activities (waitTimeInSeconds: 1) serve as fan-in synchronisation points. A single Wait activity lists every parallel SP in its dependsOn, so the next phase only needs to depend on the one Wait rather than listing every SP individually. They also visually segment the canvas into phases, making the pipeline easier to read.

**Note:** Use Wait only as a synchronisation tool or visual separator. Do not use Wait for timing delays in production flows.

### 9.3 Fact Dependencies

Not all facts are independent. When a fact table depends on the output of another (e.g. a summary built on a base fact), model this explicitly: the dependent fact's dependsOn lists the base fact activity directly, not the Wait. Independent facts all start together after the DQA gate.

### 9.4 Script Activity Standard Policy

Use a consistent policy block on every Script activity:

- timeout: 0.12:00:00 (12 hours — generous for long-running SPs).

- retry: 0 (no automatic retries; SP failures should be investigated, not silently retried).

- scriptBlockExecutionTimeout: 02:00:00 (2 hours per individual script block).

## 10. Top-Level Orchestration

The orchestration layer coordinates multiple domains. Its pipelines contain no data logic -- only ExecutePipeline and Wait activities. Each domain has a dedicated run pipeline (PL_Run_<Domain>_Bronze, PL_Run_<Domain>_Gold) and a scheduled entry point (PL_<Domain>_Daily_Run) in the Schedule_Runs folder.

### 10.1 Domain Separation

Keep each domain's Bronze and Gold in separate pipelines. This allows individual domains to be triggered, rerun, or disabled independently without touching the main daily run orchestrator.

### 10.2 Cross-Domain Dependencies

When domain B's Gold layer depends on domain A completing, model this in the top-level orchestration pipeline. Domain A and B's Bronze can run in parallel; B's Gold pipeline dependsOn both A's Gold completion and B's own Bronze completion.

Domain A Bronze --> Domain A Gold ----+

+--> Domain B Gold

Domain B Bronze ----------------------------+

**Example:** In PL_Daily_Run, Gas Bronze runs in parallel with Electricity Bronze. Gas Gold depends on both Gas Bronze Succeeded and Electricity Gold Succeeded.

### 10.3 Wait Activities as Visual Domain Separators

In orchestration pipelines with multiple parallel domain routes, insert a Wait activity (waitTimeInSeconds: 1) at the start of each route named "RUN <Domain>". This makes the canvas readable by visually anchoring where each domain chain begins.

**Example:** "RUN Electricity", "RUN Gas" -- Wait activities at the top of each domain route in PL_Daily_Run.

## 11. Working with AI on Pipeline Development

A well-documented, consistent codebase is the prerequisite for effective AI-assisted development. When an AI assistant (such as Claude) has access to the existing pipeline JSONs and a clear description of the conventions in this document, it can generate production-ready pipeline JSON for new sources -- correctly wired, correctly named, and consistent with every existing pipeline.

### 11.1 What to Give the AI

Provide the following context at the start of a session:

- This methodology document -- so the AI knows the naming conventions, folder structure, and design patterns.

- The existing pipeline JSONs for the domain closest to the new one -- as concrete templates to follow.

- The relevant management table rows for the new source -- so the AI knows the table names, keys, entity structure, and extract mode.

- The Bronze SQL file if available -- so the AI knows the exact SP signatures, table DDLs, and stage query patterns.

**Note:** The more complete the context, the less the AI has to assume. Supply real JSON files, not summaries. The AI reads structure, wiring, and expressions -- not just intent.

### 11.2 How to Write Effective Prompts

Reference the pattern by name. The AI should not need to infer the pattern from scratch each time.

Example prompt:

"Create a Master + To_Blob + To_BRONZE pipeline group for source system X,

API group Y, following the Date_Range_Params pattern.

Target table: BRONZE.BRONZE_<TABLE>. Primary keys: COL_A, COL_B.

Follow the naming conventions and folder structure from the methodology doc.

Use the attached PL_Meteo_Date_Range_Params_Master.json as a template."

### 11.3 What the AI Can Do

- Generate a full pipeline group (Master + To_Blob + To_BRONZE) from scratch, based on an existing one as a template.

- Add, remove, or reorder activities in an existing pipeline while preserving all dependsOn wiring.

- Wire a new stored procedure into a Gold pipeline at the correct phase (Dim or Fact).

- Add a new parameter to a pipeline and propagate it through all child calls.

- Wrap existing activities in a ForEach loop, or add a Lookup + IfCondition branch.

- Update folder assignments, DQA group names, or management table configuration.

- Review an existing pipeline JSON for inconsistencies with this methodology.

### 11.4 Guardrails -- Always Review Before Publishing

The AI produces JSON ready to import into ADF. Before publishing, check:

- dependsOn chains are correct and complete -- no activity starts before its inputs are ready.

- Parameter names match exactly between caller and callee parameters block.

- SP names and schema prefixes match the actual Snowflake objects.

- The folder path in the JSON matches the intended ADF folder.

- Generic datasets reference the correct linked service.

**Note:** The AI works from what it is given. If the source pipelines it was shown contain inconsistencies, it will replicate them. Keep your source pipelines clean.

## 12. Design Checklist

Use this checklist when building or reviewing an ADF pipeline group.

### Naming & Structure

- Pipeline names follow PL_<Action>_<Domain>_<Layer>.

- Suffixes are consistent and documented for the project.

- Pipelines are in the correct numbered folder.

- Shared / reusable pipelines use the GPL_ (or equivalent global) prefix.

- Activity names are descriptive and follow the conventions above.

- Parameters use P_ prefix; variables use V_ prefix.

- All parameters that have a sensible default declare a defaultValue.

### Configuration

- All API-specific attributes are in the management table.

- No table names, schema names, or entity names are hardcoded in pipeline expressions.

- The Master filters by IS_ACTIVE=1 and P_API_GROUP.

- IS_ACTIVE=0 is used to disable a source, not deleting rows or commenting out activities.

- After a successful load, the management table is updated (after DQA, not before).

### Master & ForEach

- Lookup has firstRowOnly: false.

- ForEach has isSequential: false and a reasonable batchCount.

- All ExecutePipeline activities inside ForEach have waitOnCompletion: true.

- Authentication tokens are fetched once before the ForEach, stored in a variable.

### Incremental Loading

- Delta dates are derived from LAST_TO_DAILY_DELTA.

- A special-dates override mechanism exists and sets IS_DONE=1 after use.

- For file-based sources, a file log table tracks IS_INSERT_TO_BRONZE.

### Bronze Ingestion

- Data passes through PRE_BRONZE before landing in BRONZE.

- Generic parameterised SPs are used (no one-SP-per-table).

- Script activities use the correct type: Query for SP calls, NonQuery for UPDATEs.

- DQA (duplicates + empty table) runs after every Bronze load.

- Management table is updated only after DQA passes.

### Gold

- Dims run in parallel first, then Wait sync barrier, then DQA_Dims.

- Facts start after DQA_Dims, end with Wait sync barrier, then DQA_Facts.

- If the domain has SERVE views: DQA_Others on them, after DQA_Facts (no load step).

- Fact-to-fact dependencies are explicit in dependsOn (not hidden behind the Wait).

- All Script activities use the standard policy (timeout 12h, retry 0, scriptBlockTimeout 2h).

### DQA

- DQA definitions live in a management table, not hardcoded in pipelines.

- GPL_DQA_Group is called with the correct group name at each layer gate.

- Adding a new DQA check requires only a new row in the config table.
