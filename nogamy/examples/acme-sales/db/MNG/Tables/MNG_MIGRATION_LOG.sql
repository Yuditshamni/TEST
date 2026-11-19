--------------------------------------------------------
-- MNG.MNG_MIGRATION_LOG
-- The migration history of this environment. One row per migration file.
-- Written only by tools/run_migrations.py; created by migration 0001 (--print-log-ddl). Rows are never deleted.
--   Pending here:  SELECT RUN_ORDER, FILE_NAME FROM MNG.MNG_MIGRATION_LOG WHERE IS_EXECUTED = 0 ORDER BY RUN_ORDER;
--------------------------------------------------------
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
