--------------------------------------------------------
-- QA.QA_DQA_QUERY
-- DQA framework: one row per registered check. Base method §4a.2.
-- DQA_TYPE: Duplicates / Empty_Table / Others.
-- Fail when RESULT_COUNT > THRESHOLD. Empty_Table counts as COUNT(*) * -1 (threshold -1 = fail if empty).
-- Others: DQA_QUERY returns rows only when there is a problem.
-- Schema QA (Nogamy convention), not MNG as in the base.
--------------------------------------------------------
CREATE TABLE QA.QA_DQA_QUERY
(
    GROUP_NAME  VARCHAR(100)  NOT NULL,
    DQA_TYPE    VARCHAR(20)   NOT NULL,
    TABLE_NAME  VARCHAR(200)  NOT NULL,
    TABLE_KEYS  VARCHAR(500)  NULL,
    DQA_QUERY   VARCHAR(8000) NULL,
    THRESHOLD   INT           NOT NULL,
    IS_ACTIVE   INT           NOT NULL
);
