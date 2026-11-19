--------------------------------------------------------
-- MNG.MNG_MIGRATION_LOG
-- The migration history of this environment, inside the warehouse. One row per migration file.
-- Written only by tools/migrate/run_migrations.py:
--   every file in scripts/migrations/ is registered with IS_EXECUTED = 0;
--   pending files run in RUN_ORDER (the file number), lowest first;
--   on success IS_EXECUTED = 1, EXECUTED_AT, EXECUTED_BY; on failure ERROR_MSG and the run stops.
-- Rows are never deleted.
--   Pending here:  SELECT * FROM MNG.MNG_MIGRATION_LOG WHERE IS_EXECUTED = 0 ORDER BY RUN_ORDER;
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
