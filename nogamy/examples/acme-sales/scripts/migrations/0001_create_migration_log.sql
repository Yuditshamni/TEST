-- migration: 0001
-- PR: example
-- Creates the MNG schema and the migration log MNG.MNG_MIGRATION_LOG, exactly as tools/run_migrations.py --print-log-ddl prints it.
IF SCHEMA_ID('MNG') IS NULL EXEC('CREATE SCHEMA MNG');
GO
IF OBJECT_ID('MNG.MNG_MIGRATION_LOG') IS NULL
CREATE TABLE MNG.MNG_MIGRATION_LOG
(
    RUN_ORDER      INT           NOT NULL,
    FILE_NAME      VARCHAR(200)  NOT NULL,
    DESCRIPTION    VARCHAR(500)  NULL,
    IS_EXECUTED    INT           NOT NULL,
    EXECUTED_AT    DATETIME2(6)  NULL,
    EXECUTED_BY    VARCHAR(200)  NULL,
    REGISTERED_AT  DATETIME2(6)  NOT NULL,
    ERROR_MSG      VARCHAR(4000) NULL
);
