--------------------------------------------------------
-- MNG.MNG_BRONZE_GOLD_DELTA
-- Watermark: one row per bronze -> gold pair. Base method §3a.4 (company standard).
-- The gold load procedure sets MAX_CONFIRMED_BRONZE_TS inside its transaction, only on success.
-- A bronze row is flipped to IS_LAST_INSERT_TO_BRONZE_IND = 0 only after ALL its gold tables confirmed it.
-- Rows are not deployed: scripts/seed/.
--------------------------------------------------------
CREATE TABLE MNG.MNG_BRONZE_GOLD_DELTA
(
    BRONZE_TABLE_NAME        VARCHAR(200) NOT NULL,
    GOLD_TABLE_NAME          VARCHAR(200) NOT NULL,
    MAX_CONFIRMED_BRONZE_TS  DATETIME2(6) NULL,
    ETL_UPDATE_DATE          DATETIME2(6) NULL
);
