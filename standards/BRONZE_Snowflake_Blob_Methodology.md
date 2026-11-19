<!-- converted to Markdown from BRONZE_Snowflake_Blob_Methodology.docx on 2026-10-20; original kept outside the repo -->

DWH Methodology — BRONZE Layer

Snowflake & Azure Blob Storage Integration

## 1. Purpose

This document is a supplement to 01_BRONZE_Layer_Methodology.docx. It covers the Snowflake-specific implementation for loading data from Azure Blob Storage into the BRONZE layer — the infrastructure objects, control tables, staging patterns, and generic stored procedures that implement the design described in the base document.

The following topics are fully covered in the main DWH Methodology document and are NOT repeated here. This document is a specific extension of that base — it adds the Snowflake and Azure Blob implementation details on top of the design principles already documented there.

- MNG.MNG_BRONZE_Configuration — control table for all Bronze sources.

- PRE_BRONZE staging pattern — logical design and two-SP load flow.

- IS_LAST_INSERT_TO_BRONZE_IND — the Bronze–Silver contract.

- MNG.MNG_BRONZE_GOLD_DELTA — watermark table and failure protection.

## 2. Azure Blob Storage — Folder Structure

ADF writes files to Azure Blob Storage before Snowflake picks them up. All files land under the container the external stage points to, organized by source system, logical group, and source name. The path may also include date segments for incremental sources.

### 2.1 General Pattern

Raw_Data/{SourceSystem}/{Source_Group}/{Source_Name}/

Raw_Data/{SourceSystem}/{Source_Group}/{Source_Name}/{YYYY}/{YYYY-MM}/{YYYY-MM-DD}/

The depth depends on the extract mode. Full-refresh tables use a shorter path. Daily incremental tables add a year/month/day partition for easy date-range scanning. Snowflake reads the path using METADATA$FILENAME and extracts each segment with SPLIT_PART.

Some sources add an additional sub-folder between Source_Name and the date segments (for example, a per-entity sub-path). This is a source-specific convention, not a general requirement.

### 2.2 Path Segment Mapping

| **Path Position (SPLIT_PART ,'/' , N)** | **Content** | **Example** |
|---|---|---|
| 3 | Source_Group — logical grouping within the source system | Dates_Metadata / Delta_Month_And_Entity / Daily_Dynamic_Insert |
| 4 | Source_Name — specific table or data type within the group | Special_Days / Load_plan / Actual_Generation |
| 5 (daily tables) | FILE_Year | YYYY |
| 6 (daily tables) | FILE_Month | YYYY-MM |
| 7 (daily tables) | FILE_Day | YYYY-MM-DD |
| 8 (daily tables) | FILE_Name | Page_1.json |

## 3. Infrastructure Objects

### 3.1 External Stage

All data lands in one external stage: BRONZE.MY_ADF_STAGE. This is an Azure Blob external stage created once and reused by every Bronze load SP. ADF writes files to the blob container; Snowflake SPs query the stage directly using SELECT from @BRONZE.my_adf_stage/<path>.

-- Stage is referenced as:

@BRONZE.my_adf_stage/Raw_Data/{SourceSystem}/{Source_Group}/{Source_Name}/

-- Files are scanned at query time; no COPY INTO is used for JSON sources.

-- The $1 pseudo-column holds the entire file content as a VARIANT.

Snowflake reads files directly from the stage at query time using the SELECT ... FROM @stage pattern. No COPY INTO is needed for the Raw_Data layer. COPY INTO is only used for specific sources (e.g. NATGAS XML).

### 3.2 File Formats

File format objects are defined on the BRONZE schema — one per file type. Additional formats can be added as new source types are onboarded. The standard set covers the most common cases:

| **Object** | **Format** | **Used For** |
|---|---|---|
| BRONZE.MY_JSON_FF | JSON (STRIP_OUTER_ARRAY = FALSE) | All JSON sources loaded via the stage. |
| BRONZE.MY_CSV_FF | CSV with custom delimiter and header skip | External file sources (CSV format). |
| BRONZE.MY_XML_FF | XML | Source-specific XML files. The object name may carry a source-specific suffix in practice. |

## 4. MNG.MNG_API_Configuration

MNG_API_Configuration is the primary control table for Bronze loads. It is the Snowflake counterpart to what MNG_BRONZE_Configuration describes at the abstract level. Each row represents one source/entity combination. ADF reads this table to build the request (URL, body, date window), and Snowflake SPs read it to determine what to load and from where.

### 4.1 DDL

CREATE OR REPLACE TABLE MNG.MNG_API_Configuration

(

PROJECT_NAME VARCHAR(100),

Source_System VARCHAR(100),

API_Group VARCHAR(100),

API_Name VARCHAR(100),

Extract_Mode VARCHAR(100),

Entity_Name VARCHAR(100),

API_Relative_URL VARCHAR,

API_Body VARCHAR,

Last_Blob_Folder VARCHAR,

Target_Table_Name VARCHAR,

Target_Table_Keys VARCHAR,

Last_Delta_Month_STR VARCHAR(50),

Last_From_Daily_Delta VARCHAR(50),

Last_To_Daily_Delta VARCHAR(50),

IS_SOLAR_HYBRID_ONLY INT,

Last_Insert_To_Blob_DateTime TIMESTAMP_TZ,

Last_Insert_To_BRONZE_DateTime TIMESTAMP_TZ,

Is_Active INT

);

### 4.2 Column Reference

| **Column** | **Purpose** |
|---|---|
| PROJECT_NAME | Top-level domain / project this source belongs to. |
| Source_System | The system that produces the data (e.g. the external platform or vendor). |
| API_Group | Logical grouping within the source system. Determines which blob sub-path to scan and which generic SP to call. Named API_Group in the DDL; conceptually it is the Source_Group in the folder path. |
| API_Name | Specific table or data type within the group. Named API_Name in the DDL; conceptually it is the Source_Name in the folder path. |
| Extract_Mode | Controls the loading strategy. See section 8 for details. |
| Entity_Name | Business entity for sources that deliver separate files per entity. Set to "Irrelevant" when no entity dimension exists. This is a source-specific pattern, not a general requirement. |
| API_Relative_URL | Relative URL template used by ADF to call the source system. ADF substitutes runtime placeholders before sending the request. |
| API_Body | Request body template for POST-based sources. ADF substitutes placeholders before the call. |
| Last_Blob_Folder | Last blob folder path written by ADF. Used by sources that do not use date-partitioned paths. |
| Target_Table_Name | Short name of the Bronze table (without schema prefix). |
| Target_Table_Keys | Comma-separated logical key columns. Used for duplicate DQA checks. |
| Last_Delta_Month_STR | Last successfully loaded month (YYYY-MM). Used by Delta_Month SPs to compute the load window. |
| Last_From_Daily_Delta | Start of the last successfully loaded daily window. Used by Date_Range and Daily_Insert SPs. |
| Last_To_Daily_Delta | End of the last successfully loaded daily window. |
| IS_SOLAR_HYBRID_ONLY | Project-specific flag (example). Shows that domain-specific columns can be added to this table. |
| Last_Insert_To_Blob_DateTime | Timestamp when ADF last wrote a file for this row. Updated by ADF after each successful upload. |
| Last_Insert_To_BRONZE_DateTime | Timestamp when a Snowflake SP last inserted rows into Bronze for this row. |
| Is_Active | 1 = included in pipeline runs. 0 = skipped without removing the config row. |

## 5. MNG.MNG_API_SPECIAL_DATES_DELTA_RUN

This table is used to override the normal date window for a one-off re-load. Instead of using Last_From_Daily_Delta / Last_To_Daily_Delta from MNG_API_Configuration, the pipeline checks this table first. If an unprocessed row (IS_DONE = 0) exists for the relevant source/entity combination, it uses SPECIAL_FROM_DAILY_DELTA and SPECIAL_TO_DAILY_DELTA as the load window for that run.

After the load completes, ADF sets IS_DONE = 1. The row is kept for audit; it is never deleted.

CREATE OR REPLACE TABLE MNG.MNG_API_SPECIAL_DATES_DELTA_RUN

(

PROJECT_NAME VARCHAR(100),

API_Group VARCHAR(100),

API_Name VARCHAR(100),

Entity_Name VARCHAR(100),

SPECIAL_FROM_DAILY_DELTA VARCHAR(50),

SPECIAL_TO_DAILY_DELTA VARCHAR(50),

Last_Insert_To_Blob_DateTime TIMESTAMP_TZ,

Is_Done INT

);

## 6. MNG.MNG_BLOB_FILES_LOG

MNG_BLOB_FILES_LOG is the file-level tracking log. ADF writes one row per file immediately after uploading each file to blob. Snowflake SPs JOIN this table to the stage scan to select only files that have not yet been loaded into Bronze.

CREATE OR REPLACE TABLE MNG.MNG_BLOB_FILES_LOG

(

API_GROUP VARCHAR(100),

API_NAME VARCHAR(100),

ENTITY_NAME VARCHAR(100),

File_DELTA VARCHAR(50),

CURRENT_RUN_FROM_DAILY_DELTA VARCHAR(50),

CURRENT_RUN_TO_DAILY_DELTA VARCHAR(50),

File_Full_Path VARCHAR,

LAST_INSERT_TO_BLOB_DATETIME TIMESTAMP_TZ,

PL_RUN_ID VARCHAR,

IS_INSERT_TO_BRONZE NUMBER

);

### 6.1 How the Log Is Used

ADF populates this log after every file upload: IS_INSERT_TO_BRONZE = 0 on insert. Snowflake SPs JOIN to the log and filter IS_INSERT_TO_BRONZE = 0 to load only new files. After a successful Bronze load, ADF (or the orchestrating pipeline) sets IS_INSERT_TO_BRONZE = 1 on the processed rows.

This is the primary mechanism for incremental file-level loading in Daily_Insert and Date_Range sources. A file is never loaded twice as long as IS_INSERT_TO_BRONZE is properly maintained.

When the same file path appears more than once in MNG_BLOB_FILES_LOG (re-deliveries), SPs use QUALIFY ROW_NUMBER() OVER (PARTITION BY FILE_FULL_PATH ORDER BY LAST_INSERT_TO_BLOB_DATETIME DESC) = 1 to take only the most recent entry before joining.

## 7. Two-Step PRE_BRONZE Staging (Snowflake-Specific)

The base document describes PRE_BRONZE as a single staging layer between source and Bronze. In the actual Snowflake implementation, most API sources use two staging steps before reaching Bronze:

- Step 1 — PRE_BRONZE_Raw_Data_<Name>: stores the raw JSON blob content as-is, one row per file. No parsing. The raw JSON is held in a VARIANT column called RAW_DATA.

- Step 2 — V_PRE_BRONZE_<Name> (view) + PRE_BRONZE_<Name> (table): parses the VARIANT and flattens it into typed, record-level rows. This is what the Bronze SP inserts into the BRONZE table.

### 8.1 PRE_BRONZE_Raw_Data Tables

These tables store the raw stage output. The standard column set is:

-- Path metadata extracted from METADATA$FILENAME using SPLIT_PART:

Source_Group VARCHAR -- SPLIT_PART(METADATA$FILENAME,'/',N) -- Source_Group segment

Source_Name VARCHAR -- SPLIT_PART(METADATA$FILENAME,'/',N) -- Source_Name segment

File_Full_Path VARCHAR -- METADATA$FILENAME (full blob path)

FILE_Name VARCHAR -- SPLIT_PART(METADATA$FILENAME,'/',N) -- last segment

raw_data VARIANT -- $1 (entire file as a single JSON value)

insert_timestamp TIMESTAMP_NTZ -- CURRENT_TIMESTAMP() at load time

IS_INSERT_TO_PRE_BRONZE_IND INT -- 0 on insert (not yet moved to PRE_BRONZE)

Daily-partitioned sources also store FILE_Year, FILE_Month, FILE_Day extracted from the path. Full-refresh sources (shorter paths) do not need these.

### 8.2 METADATA$FILENAME — Virtual Path Column

Snowflake exposes the full blob file path as METADATA$FILENAME when querying an external stage. This is not a column in the file — it is a system-provided pseudo-column available only inside the FROM @stage clause. It is used for two purposes:

- Extracting path metadata (Source_Group, Source_Name, date segments) using SPLIT_PART.

- Joining to MNG_BLOB_FILES_LOG to select only unprocessed files (JOIN on File_Full_Path = METADATA$FILENAME AND IS_INSERT_TO_BRONZE = 0).

### 8.3 JSON Parsing in V_PRE_BRONZE Views

Each PRE_BRONZE_Raw_Data table has a corresponding view (V_PRE_BRONZE_<Name>) that parses the VARIANT column into typed columns. Two patterns are used:

#### Flat array — one record per array element

SELECT

t.INSERT_TIMESTAMP AS Load_To_PRE_BRONZE_TS,

x.value:fieldName::STRING AS field_name,

...

FROM PRE_BRONZE.PRE_BRONZE_Raw_Data_<Name> t

CROSS JOIN LATERAL FLATTEN(input => t.RAW_DATA) AS x

#### Nested JSON — page wrapper + records array

-- API response: { pageNumber: N, amountOfPages: M, records: [...] }

FROM (

SELECT

CASE WHEN TYPEOF(RAW_DATA) = 'STRING' THEN TRY_PARSE_JSON(RAW_DATA)

ELSE RAW_DATA

END AS J,

INSERT_TIMESTAMP, ENTITY_NAME, FILE_NAME

FROM PRE_BRONZE.PRE_BRONZE_Raw_Data_<Name>

) t,

LATERAL FLATTEN(input => IFF(TYPEOF(t.J) = 'ARRAY', t.J, ARRAY_CONSTRUCT(t.J))) AS root,

LATERAL FLATTEN(input => GET_PATH(root.value, 'records')) AS rec

TRY_PARSE_JSON is applied defensively — some source responses are stored as STRING type inside the VARIANT column. TYPEOF checks the actual runtime type before parsing.

## 8. Extract Modes and Generic Stored Procedures

This section illustrates the loading patterns with representative examples. The actual SP names, parameters, and extract modes in your implementation may differ. The intent is to show the design pattern, not to document every SP exhaustively.

The EXTRACT_MODE column in MNG_API_Configuration determines which generic SPs the pipeline calls and how Snowflake filters files or date windows. Each mode maps to a fixed pair of SPs: one that loads raw files into PRE_BRONZE_Raw_Data, and one that moves parsed rows into Bronze.

All generic SPs live on the MNG schema and use EXECUTE IMMEDIATE for dynamic SQL. Parameters are the target table name, the blob path prefix, and optionally the entity name and source name for filtering.

### 8.1 Load Patterns (Examples)

The three patterns below cover the most common extract modes. Each is shown with a representative SP call.

#### Full refresh — scan all files, TRUNCATE and reload

Used when the source always sends a complete data set. PRE_BRONZE_Raw_Data is truncated on every run. The Bronze table is also fully replaced.

-- Step 1: load raw files from blob into PRE_BRONZE_Raw_Data

CALL MNG.SP_LOAD_Full_Tables_To_PRE_BRONZE_Row_Data(

P_TABLE_NAME => 'PRE_BRONZE_Raw_Data_<SourceName>',

P_FILE_PATH => 'Raw_Data/{SourceSystem}/{Source_Group}/{Source_Name}/'

);

-- Logic: TRUNCATE PRE_BRONZE.<P_TABLE_NAME>

-- INSERT from @BRONZE.my_adf_stage/<P_FILE_PATH>

-- using METADATA$FILENAME for path columns, $1 for raw_data

-- Step 2: parse and load into Bronze

CALL MNG.SP_LOAD_Full_Tables_To_BRONZE(P_SCHEMA => 'BRONZE', P_TABLE => 'BRONZE_<SourceName>');

-- Logic: TRUNCATE BRONZE.<P_TABLE>

-- INSERT INTO BRONZE.<P_TABLE> SELECT * FROM BRONZE.V_<P_TABLE>

#### Delta_Month — incremental monthly window

Used for sources where files are named by month (YYYY-MM prefix). The SP deletes existing rows for the entity and reloads starting from LAST_DELTA_MONTH_STR - 1 month (one extra month as a safety buffer).

-- Step 1: incremental load into PRE_BRONZE_Raw_Data

CALL MNG.SP_LOAD_INC_Tables_To_PRE_BRONZE_Row_Data(

P_TABLE_NAME => 'PRE_BRONZE_Raw_Data_<SourceName>',

P_FILE_PATH => 'Raw_Data/{SourceSystem}/{Source_Group}/{Source_Name}/',

P_ENTITY_NAME => '<EntityName>',

P_SOURCE_NAME => '<SourceName>'

);

-- File filter inside the dynamic INSERT:

-- WHERE LEFT(FILE_NAME, 7) >= (

-- SELECT TO_CHAR(ADD_MONTHS(TO_DATE(LAST_DELTA_MONTH_STR||'-01'), -1), 'YYYY-MM')

-- FROM MNG.MNG_API_CONFIGURATION

-- WHERE ENTITY_NAME = P_ENTITY_NAME AND API_NAME = P_SOURCE_NAME

-- )

-- Step 2: move parsed rows to Bronze (DELETE+INSERT per entity)

CALL MNG.SP_LOAD_FULL_TABLES_PER_ENTITY_TO_BRONZE(

P_SCHEMA => 'BRONZE',

P_TABLE => 'BRONZE_<SourceName>',

P_ENTITY_NAME => '<EntityName>'

);

-- Logic: DELETE FROM BRONZE.<P_TABLE> WHERE ENTITY_NAME = P_ENTITY_NAME

-- INSERT INTO BRONZE.<P_TABLE> SELECT * FROM BRONZE.V_<P_TABLE>

-- WHERE ENTITY_NAME = P_ENTITY_NAME

#### Daily_Insert / Date_Range — file-log-driven incremental

Used for sources where files arrive daily and are tracked in MNG_BLOB_FILES_LOG. The SP selects only files with IS_INSERT_TO_BRONZE = 0 in the log, preventing double-loads. A QUALIFY ROW_NUMBER() deduplicates re-delivered files before the JOIN.

-- Step 1: load unprocessed files into PRE_BRONZE_Raw_Data

CALL MNG.SP_LOAD_INC_Tables_By_Files_Log_To_PRE_BRONZE_Row_Data(

P_TABLE_NAME => 'PRE_BRONZE_Raw_Data_<SourceName>',

P_FILE_PATH => 'Raw_Data/{SourceSystem}/{Source_Group}/{Source_Name}/',

P_ENTITY_NAME => '<EntityName>',

P_SOURCE_NAME => '<SourceName>'

);

-- Key join pattern inside the dynamic INSERT:

-- JOIN (SELECT * FROM MNG.MNG_BLOB_FILES_LOG

-- QUALIFY ROW_NUMBER() OVER (PARTITION BY FILE_FULL_PATH

-- ORDER BY LAST_INSERT_TO_BLOB_DATETIME DESC) = 1) L

-- ON A.File_Full_Path = L.File_Full_Path

-- AND L.IS_INSERT_TO_BRONZE = 0

-- Step 2: incremental Bronze load — deduplicates by DATE + ENTITY

CALL MNG.SP_LOAD_INC_TABLES_PER_Date_And_ENTITY_TO_BRONZE(

P_SCHEMA => 'BRONZE',

P_SOURCE_TABLE => 'BRONZE_<SourceName>_<Entity>',

P_TARGET_TABLE => 'BRONZE_<SourceName>',

P_ENTITY_NAME => '<EntityName>'

);

-- Logic:

-- 1) UPDATE BRONZE.<TARGET> SET IS_LAST_INSERT_TO_BRONZE_IND = 0 WHERE ENTITY_NAME = P_ENTITY_NAME

-- 2) DELETE FROM BRONZE.<TARGET> WHERE (DATE, ENTITY_NAME) exists in V_<SOURCE>

-- 3) INSERT INTO BRONZE.<TARGET> SELECT * FROM BRONZE.V_<SOURCE> WHERE ENTITY_NAME = P_ENTITY_NAME

A variant of the daily-increment SP (SP_LOAD_INC_TABLES_PER_Date_Time_And_ENTITY_TO_BRONZE) deduplicates on TIME_FROM + ENTITY_NAME instead of DATE. Used when the grain is a timestamp range and multiple rows per date exist.

### 8.2 Dynamic PIVOT Transform

Some sources deliver data in long format — one row per field name and value (FIELD_NAME, FIELD_VALUE columns). SP_LOAD_Dynamic_PIVOT builds a wide pivoted table or view dynamically by reading the distinct FIELD_NAME values at runtime and generating a MAX(CASE WHEN ...) expression for each one.

CALL MNG.SP_LOAD_Dynamic_PIVOT(

TARGET_OBJECT => 'PRE_BRONZE.PRE_BRONZE_<SourceName>_UNPIVOT_<Entity>',

AS_VIEW => FALSE, -- TRUE to create a view instead of a table

SOURCE_TABLE => 'PRE_BRONZE.PRE_BRONZE_<SourceName>',

P_PIVOT_1 => '<GroupCol>', -- primary grouping column alias

P_PIVOT_2 => NULL, -- optional secondary grouping column

P_PIVOT_3_BID_OFFER => NULL, -- optional bid/offer level column

P_ENTITY_NAME => '<EntityName>' -- optional entity filter (NULL for no filter)

);

-- Output: one wide table or view per entity with one column per distinct FIELD_NAME value.

-- CLOCK_CHANGE_SEPARATOR column flags duplicate time slots from DST transitions.

## 9. IS_LAST_INSERT_TO_BRONZE_IND — Snowflake Implementation

The IS_LAST contract is defined in the base document. In the Snowflake code, IS_LAST = 1 is set in the V_PRE_BRONZE views (hardcoded literal in the SELECT), not in the SP. Every row inserted from a view carries IS_LAST = 1.

The IS_LAST = 0 update happens in the Bronze-level SPs (10.7 and 10.8) as the first step before the DELETE + INSERT. This ensures old rows for the same entity are marked as historical before the new batch is inserted.

For source-specific Bronze SPs, the IS_LAST update may be implicit — the entire entity is replaced via DELETE + INSERT, so all surviving rows come from the current batch and implicitly represent IS_LAST = 1.

## 10. Summary

| **Component** | **Object** | **Role** |
|---|---|---|
| External stage | BRONZE.MY_ADF_STAGE | Single Azure Blob stage. All source files land here. Queried directly using SELECT from @stage. |
| File formats | MY_JSON_FF / MY_CSV_FF / MY_XML_FF_NATGAS | Define how Snowflake reads each file type from the stage. |
| Source config | MNG.MNG_API_Configuration | One row per source/entity. Controls extract mode, date window, blob path, target table. |
| Special dates | MNG.MNG_API_SPECIAL_DATES_DELTA_RUN | One-off date range overrides. ADF checks this before using the standard window. |
| File log | MNG.MNG_BLOB_FILES_LOG | One row per uploaded file. IS_INSERT_TO_BRONZE = 0 marks unprocessed files. SPs JOIN here to select new files only. |
| Raw staging | PRE_BRONZE.PRE_BRONZE_Raw_Data_<Name> | Raw JSON VARIANT. One row per file. Loaded by the appropriate generic SP based on extract mode. |
| Parsed staging | PRE_BRONZE.V_PRE_BRONZE_<Name> | View that FLATTENs the VARIANT and casts all columns. Source for the PRE_BRONZE materialized table. |
| Materialized staging | PRE_BRONZE.PRE_BRONZE_<Name> | Table populated from the view. Source for Bronze SP. |
| Bronze load | BRONZE.BRONZE_<Name> | Final Bronze table. Loaded by generic SP based on extract mode, or source-specific SP. |
| Pivot transform | MNG.SP_LOAD_Dynamic_PIVOT | Dynamically builds wide pivoted tables from FIELD_NAME / FIELD_VALUE long format. |

Version: 1.0 | June 2026
