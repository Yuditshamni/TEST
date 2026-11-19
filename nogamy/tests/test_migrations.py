"""Offline tests of tools/run_migrations.py: SQL splitting, run sheet, log DDL, and a full run on SQLite."""
import sqlite3
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(sys.argv[1]).resolve() if len(sys.argv) > 1 else Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools"))
import run_migrations as rm  # noqa: E402

fails = 0


def check(title, cond, extra=""):
    global fails
    fails += not cond
    print(("PASS " if cond else "FAIL ") + title + (f"  [{extra}]" if extra and not cond else ""))


# 1. splitting
snow = """CREATE TABLE IF NOT EXISTS GOLD.T (A INT, B VARCHAR(10));
INSERT INTO GOLD.T VALUES (1, 'a;b'), (2, 'it''s; ok');  -- a ; in a comment
CREATE OR REPLACE PROCEDURE MNG.P() RETURNS STRING LANGUAGE SQL AS
$$
BEGIN
  INSERT INTO GOLD.T VALUES (3, 'x'); RETURN 'done';
END;
$$;
/* block; comment */
"""
parts = rm.split_sql(snow, "sql")
check("sql split: 3 statements (quotes, comments, $$ body kept whole)", len(parts) == 3, str(len(parts)))
check("sql split: the procedure body is one statement", "RETURN 'done';" in parts[2])
tsql = "CREATE TABLE GOLD.T (A INT);\nGO\nINSERT INTO GOLD.T VALUES (1);\nINSERT INTO GOLD.T VALUES (2);\ngo\n-- only a comment\n"
check("tsql split: GO batches (2)", len(rm.split_sql(tsql, "tsql")) == 2)
pg = "CREATE FUNCTION f() RETURNS int AS $body$ SELECT 1; $body$ LANGUAGE sql;\nSELECT f();"
check("postgres split: $tag$ body (2)", len(rm.split_sql(pg, "sql")) == 2)

# 2. DDL and run sheet per dialect
for name, d in rm.DIALECTS.items():
    ddl = rm.log_ddl(d)
    check(f"log DDL {name}: has the 8 columns", all(c in ddl for c in (
        "RUN_ORDER", "FILE_NAME", "DESCRIPTION", "IS_EXECUTED", "EXECUTED_AT", "EXECUTED_BY", "REGISTERED_AT", "ERROR_MSG")))

# 3. a full run on SQLite (a test dialect: MNG is an attached database)
tmp = Path(tempfile.mkdtemp())
rm.FOLDER = tmp
rm.DIALECTS["test"] = {"exists": "SELECT COUNT(*) FROM MNG.sqlite_master WHERE name = 'MNG_MIGRATION_LOG'",
                       "now": "CURRENT_TIMESTAMP", "user": "'tester'", "batches": "sql",
                       "ts": "TIMESTAMP", "str": "VARCHAR({n})", "schema": "", "create": "CREATE TABLE IF NOT EXISTS MNG.MNG_MIGRATION_LOG"}
rm.PLATFORM_DIALECT["test"] = "test"
ddl = rm.log_ddl(rm.DIALECTS["test"])
(tmp / "0001_create_log.sql").write_text(f"-- migration: 0001\n-- PR: test\n-- Creates the migration log.\n{ddl}\n", encoding="utf-8")
(tmp / "0002_gold_customer.sql").write_text("-- migration: 0002\n-- Adds GOLD.DIM_CUSTOMER.\n"
                                           "CREATE TABLE IF NOT EXISTS GOLD.DIM_CUSTOMER (CUSTOMER_KEY INT, NAME VARCHAR(50));\n", encoding="utf-8")
(tmp / "0003_seed.sql").write_text("-- migration: 0003\n-- Adds the -99 row; safe twice.\n"
                                   "INSERT INTO GOLD.DIM_CUSTOMER SELECT -99, 'unknown; none' "
                                   "WHERE NOT EXISTS (SELECT 1 FROM GOLD.DIM_CUSTOMER WHERE CUSTOMER_KEY = -99);\n", encoding="utf-8")
conn = sqlite3.connect(":memory:", isolation_level=None)
conn.execute("ATTACH ':memory:' AS MNG")
conn.execute("ATTACH ':memory:' AS GOLD")
dev = {"platform": "test", "environment": "DEV", "agent": True}
check("--check on the test files: ok", rm.check_files() == [], str(rm.check_files()))
code = rm.apply(dev, conn=conn)
log = conn.execute("SELECT RUN_ORDER, IS_EXECUTED, EXECUTED_BY, DESCRIPTION FROM MNG.MNG_MIGRATION_LOG ORDER BY 1").fetchall()
check("first run: 3 executed, logged with user and description",
      code == 0 and [r[:3] for r in log] == [(1, 1, "tester"), (2, 1, "tester"), (3, 1, "tester")] and log[1][3] == "Adds GOLD.DIM_CUSTOMER.", str(log))
rm.apply(dev, conn=conn)
check("second run: nothing pending, -99 row once",
      conn.execute("SELECT COUNT(*) FROM GOLD.DIM_CUSTOMER WHERE CUSTOMER_KEY = -99").fetchone()[0] == 1)
rm.apply(dev, rerun=3, conn=conn)
check("--rerun 3 in DEV: still one -99 row (the file is safe twice)",
      conn.execute("SELECT COUNT(*) FROM GOLD.DIM_CUSTOMER").fetchone()[0] == 1)

(tmp / "0004_broken.sql").write_text("-- migration: 0004\n-- Breaks on purpose.\nINSERT INTO GOLD.NO_SUCH_TABLE VALUES (1);\n", encoding="utf-8")
(tmp / "0005_after.sql").write_text("-- migration: 0005\n-- Must not run after a failure.\nCREATE TABLE GOLD.AFTER (A INT);\n", encoding="utf-8")
try:
    rm.apply(dev, conn=conn); stopped = False
except SystemExit as e:
    stopped = "FAILED: 0004_broken.sql" in str(e)
row4 = conn.execute("SELECT IS_EXECUTED, ERROR_MSG FROM MNG.MNG_MIGRATION_LOG WHERE RUN_ORDER = 4").fetchone()
after = conn.execute("SELECT COUNT(*) FROM GOLD.sqlite_master WHERE name = 'AFTER'").fetchone()[0]
check("failure: stops, ERROR_MSG written, 0005 not run", stopped and row4[0] == 0 and "NO_SUCH_TABLE" in (row4[1] or "") and after == 0, str(row4))

(tmp / "0004_broken.sql").write_text("-- migration: 0004\n-- Removes an old table.\nDROP TABLE IF EXISTS GOLD.OLD;\n", encoding="utf-8")
try:
    rm.apply(dev, as_agent=True, conn=conn); refused = False
except SystemExit as e:
    refused = "refusing --as-agent: DROP" in str(e)
check("agent: refuses a pending DROP before anything runs", refused and after == 0)
for env, title in (({"platform": "test", "environment": "PROD", "agent": True}, "agent on PROD"),
                   ({"platform": "test", "environment": "DEV"}, "agent without agent: true")):
    try:
        rm.apply(env, as_agent=True, conn=conn); ok = False
    except SystemExit as e:
        ok = "refusing --as-agent" in str(e)
    check(f"{title}: refused", ok)
try:
    rm.apply({"platform": "test", "environment": "PROD"}, rerun=2, conn=conn); ok = False
except SystemExit as e:
    ok = "DEV only" in str(e)
check("--rerun on PROD: refused", ok)

sheet = rm.run_sheet(rm.DIALECTS["snowflake"], rm.migration_files(), 4)
check("run sheet (snowflake, from 0004): steps 0004 and 0005, Snowflake log words, no 0001",
      "Step 0004" in sheet and "Step 0005" in sheet and "CURRENT_USER()" in sheet and "Step 0001" not in sheet)

# 4. the command line, on the real repo (no migrations yet)
r = subprocess.run([sys.executable, str(ROOT / "tools/run_migrations.py"), "--check"], capture_output=True, text=True)
check("CLI --check on scripts/migrations/: ok", r.returncode == 0, r.stdout + r.stderr)
r = subprocess.run([sys.executable, str(ROOT / "tools/run_migrations.py"), "--platform", "snowflake", "--print-log-ddl"],
                   capture_output=True, text=True)
check("CLI --print-log-ddl snowflake", r.returncode == 0 and "TIMESTAMP_NTZ" in r.stdout, r.stderr)
r = subprocess.run([sys.executable, str(ROOT / "tools/run_migrations.py"), "--platform", "oracle", "--run-sheet"],
                   capture_output=True, text=True)
check("CLI unknown platform: clear message, no crash", r.returncode != 0 and "no dialect" in (r.stderr + r.stdout))
print("FAILS:", fails)
sys.exit(1 if fails else 0)
