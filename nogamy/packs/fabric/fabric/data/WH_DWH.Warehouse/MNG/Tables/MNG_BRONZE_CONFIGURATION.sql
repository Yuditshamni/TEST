--------------------------------------------------------
-- MNG.MNG_BRONZE_CONFIGURATION
-- One row per bronze source table. Drives the bronze Master pipelines.
-- Base method §3a.1. Columns as in the nogamy-bronze-load skill.
-- SOURCE_QUERY: project addition. The SELECT the Copy Activity sends to the source,
-- so no source-specific text sits in the pipeline JSON.
-- IS_MASS_DELETE_APPROVED: 1 releases the mass-delete guard of BRONZE.SP_LOAD_BRONZE for one run; a successful run resets it.
-- Rows are not deployed: scripts/seed/. Disable a row with IS_ACTIVE = 0, never delete it.
--------------------------------------------------------
CREATE TABLE MNG.MNG_BRONZE_CONFIGURATION
(
    SOURCE_SYSTEM                           VARCHAR(100)  NOT NULL,
    SOURCE_GROUP                            VARCHAR(100)  NOT NULL,
    SOURCE_NAME                             VARCHAR(200)  NOT NULL,
    SOURCE_QUERY                            VARCHAR(8000) NULL,
    EXTRACT_MODE                            VARCHAR(20)   NOT NULL,
    TARGET_TABLE_NAME                       VARCHAR(200)  NOT NULL,
    TARGET_TABLE_KEYS                       VARCHAR(500)  NULL,
    LAST_FROM_DELTA                         DATETIME2(0)  NULL,
    LAST_TO_DELTA                           DATETIME2(0)  NULL,
    LAST_BUSINESS_SUCCESSFUL_LOAD_DATETIME  DATETIME2(0)  NULL,
    LAST_INSERT_TO_BRONZE_DATETIME          DATETIME2(0)  NULL,
    IS_ACTIVE                               INT           NOT NULL,
    IS_MASS_DELETE_APPROVED                 INT           NULL
);
