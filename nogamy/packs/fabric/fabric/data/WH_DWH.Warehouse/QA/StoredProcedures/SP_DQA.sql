--------------------------------------------------------
-- QA.SP_DQA
-- DQA engine. Base method §4a.4. Runs checks, writes QA.QA_DQA_RESULT, fails if any check fails.
-- Two ways to call:
--   1. Registered checks: filter QA.QA_DQA_QUERY by any of the parameters (NULL = all).
--        EXEC QA.SP_DQA @GROUP_NAME = 'SALES_GOLD_Dims';
--   2. Ad hoc gate after a bronze load: @DQA_TYPE + @TABLE_NAME (+ @TABLE_KEYS), no config row needed.
--        EXEC QA.SP_DQA @DQA_TYPE = 'Duplicates', @TABLE_NAME = 'BRONZE.X', @TABLE_KEYS = 'ID';
-- Default threshold for an ad hoc check: Duplicates 0, Empty_Table -1.
-- A failed check raises error 50001, so the calling pipeline activity fails and stops.
--------------------------------------------------------
CREATE PROCEDURE QA.SP_DQA
    @DQA_TYPE    VARCHAR(20)  = NULL,
    @TABLE_NAME  VARCHAR(200) = NULL,
    @TABLE_KEYS  VARCHAR(500) = NULL,
    @GROUP_NAME  VARCHAR(100) = NULL,
    @THRESHOLD   INT          = NULL
AS
BEGIN
    SET NOCOUNT ON;

    DECLARE @RUN_TS      DATETIME2(6) = CAST(SYSUTCDATETIME() AS DATETIME2(6));
    DECLARE @I           INT = 1;
    DECLARE @N           INT;
    DECLARE @SQL         NVARCHAR(4000);
    DECLARE @CNT         INT;
    DECLARE @ERR         VARCHAR(4000);
    DECLARE @FAILED      INT;
    DECLARE @C_GROUP     VARCHAR(100);
    DECLARE @C_TYPE      VARCHAR(20);
    DECLARE @C_TABLE     VARCHAR(200);
    DECLARE @C_KEYS      VARCHAR(500);
    DECLARE @C_QUERY     VARCHAR(8000);
    DECLARE @C_THRESHOLD INT;

    CREATE TABLE #DQA_CHECKS
    (
        RN          INT,
        GROUP_NAME  VARCHAR(100),
        DQA_TYPE    VARCHAR(20),
        TABLE_NAME  VARCHAR(200),
        TABLE_KEYS  VARCHAR(500),
        DQA_QUERY   VARCHAR(8000),
        THRESHOLD   INT
    )
    WITH (DISTRIBUTION = ROUND_ROBIN);

    --------------------------------------------------------
    -- Step 1: the list of checks to run
    --------------------------------------------------------
    IF @DQA_TYPE IN ('Duplicates', 'Empty_Table') AND @TABLE_NAME IS NOT NULL
       AND NOT EXISTS (SELECT 1 FROM QA.QA_DQA_QUERY WHERE TABLE_NAME = @TABLE_NAME AND DQA_TYPE = @DQA_TYPE AND IS_ACTIVE = 1)
        INSERT INTO #DQA_CHECKS (RN, GROUP_NAME, DQA_TYPE, TABLE_NAME, TABLE_KEYS, DQA_QUERY, THRESHOLD)
        VALUES (1, @GROUP_NAME, @DQA_TYPE, @TABLE_NAME, @TABLE_KEYS, NULL,
                COALESCE(@THRESHOLD, CASE WHEN @DQA_TYPE = 'Empty_Table' THEN -1 ELSE 0 END))
    ELSE
        INSERT INTO #DQA_CHECKS (RN, GROUP_NAME, DQA_TYPE, TABLE_NAME, TABLE_KEYS, DQA_QUERY, THRESHOLD)
        SELECT ROW_NUMBER() OVER (ORDER BY Q.GROUP_NAME, Q.TABLE_NAME, Q.DQA_TYPE),
               Q.GROUP_NAME,
               Q.DQA_TYPE,
               Q.TABLE_NAME,
               Q.TABLE_KEYS,
               Q.DQA_QUERY,
               COALESCE(@THRESHOLD, Q.THRESHOLD)
        FROM   QA.QA_DQA_QUERY AS Q
        WHERE  Q.IS_ACTIVE = 1
          AND  (@DQA_TYPE   IS NULL OR Q.DQA_TYPE   = @DQA_TYPE)
          AND  (@TABLE_NAME IS NULL OR Q.TABLE_NAME = @TABLE_NAME)
          AND  (@TABLE_KEYS IS NULL OR Q.TABLE_KEYS = @TABLE_KEYS)
          AND  (@GROUP_NAME IS NULL OR Q.GROUP_NAME = @GROUP_NAME);

    SELECT @N = COUNT(*) FROM #DQA_CHECKS;

    --------------------------------------------------------
    -- Step 2: run each check, write one result row per check
    --------------------------------------------------------
    WHILE @I <= @N
    BEGIN
        SELECT @C_GROUP     = GROUP_NAME,
               @C_TYPE      = DQA_TYPE,
               @C_TABLE     = TABLE_NAME,
               @C_KEYS      = TABLE_KEYS,
               @C_QUERY     = DQA_QUERY,
               @C_THRESHOLD = THRESHOLD
        FROM   #DQA_CHECKS
        WHERE  RN = @I;

        SET @SQL = CASE @C_TYPE
            WHEN 'Duplicates'  THEN N'SELECT @CNT = COUNT(*) FROM (SELECT ' + @C_KEYS + N' FROM ' + @C_TABLE
                                    + N' GROUP BY ' + @C_KEYS + N' HAVING COUNT(*) > 1) AS D'
            WHEN 'Empty_Table' THEN N'SELECT @CNT = COUNT(*) * -1 FROM ' + @C_TABLE
            WHEN 'Others'      THEN N'SELECT @CNT = COUNT(*) FROM (' + @C_QUERY + N') AS D'
        END;

        SET @CNT = NULL;
        SET @ERR = NULL;
        BEGIN TRY
            EXEC sp_executesql @SQL, N'@CNT INT OUTPUT', @CNT = @CNT OUTPUT;
        END TRY
        BEGIN CATCH
            SET @ERR = ERROR_MESSAGE();
        END CATCH;

        INSERT INTO QA.QA_DQA_RESULT (RUN_TS, GROUP_NAME, DQA_TYPE, TABLE_NAME, TABLE_KEYS, RESULT_COUNT, THRESHOLD, PASS_IND, ERROR_MSG)
        VALUES (@RUN_TS, @C_GROUP, @C_TYPE, @C_TABLE, @C_KEYS, @CNT, @C_THRESHOLD,
                CASE WHEN @ERR IS NULL AND @CNT <= @C_THRESHOLD THEN 1 ELSE 0 END,
                @ERR);

        SET @I = @I + 1;
    END;

    --------------------------------------------------------
    -- Step 3: return this run's results; fail the caller if a check failed
    --------------------------------------------------------
    SELECT GROUP_NAME,
           DQA_TYPE,
           TABLE_NAME,
           RESULT_COUNT,
           THRESHOLD,
           PASS_IND,
           ERROR_MSG
    FROM   QA.QA_DQA_RESULT
    WHERE  RUN_TS = @RUN_TS
    ORDER BY PASS_IND, TABLE_NAME;

    SELECT @FAILED = COUNT(*) FROM QA.QA_DQA_RESULT WHERE RUN_TS = @RUN_TS AND PASS_IND = 0;

    IF @N = 0
        THROW 50002, 'SP_DQA: no check matched the parameters.', 1;
    IF @FAILED > 0
        THROW 50001, 'SP_DQA: at least one check failed. See QA.QA_DQA_RESULT for this RUN_TS.', 1;
END;
