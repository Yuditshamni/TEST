--------------------------------------------------------
-- QA.QA_DQA_RESULT
-- DQA framework: one row per executed check. Base method §4a.5.
-- Append only. Rows are never deleted: the audit trail of every run.
-- Schema QA (Nogamy convention), not MNG as in the base.
--------------------------------------------------------
CREATE TABLE QA.QA_DQA_RESULT
(
    RUN_TS        DATETIME2(6)  NOT NULL,
    GROUP_NAME    VARCHAR(100)  NULL,
    DQA_TYPE      VARCHAR(20)   NOT NULL,
    TABLE_NAME    VARCHAR(200)  NOT NULL,
    TABLE_KEYS    VARCHAR(500)  NULL,
    RESULT_COUNT  INT           NULL,
    THRESHOLD     INT           NOT NULL,
    PASS_IND      INT           NOT NULL,
    ERROR_MSG     VARCHAR(4000) NULL
);
