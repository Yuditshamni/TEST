"""tools/run_migrations.py against a real database (core CI starts one as a service container; test data only).

    NOGAMY_LIVE=postgres  PGPASSWORD=...        python nogamy/tests/test_migrations_live.py
    NOGAMY_LIVE=sqlserver NOGAMY_LIVE_PWD=...   python nogamy/tests/test_migrations_live.py

Runs a first migration set, re-runs it (nothing changes), re-runs one file in DEV (still one row),
then a failing file: the run stops, ERROR_MSG is written, nothing after it runs.
"""
import os
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools"))
import run_migrations as rm  # noqa: E402

LIVE = os.environ.get("NOGAMY_LIVE", "")
fails = 0


def check(title, cond, extra=""):
    global fails
    fails += not cond
    print(("PASS " if cond else "FAIL ") + f"[{LIVE}] {title}" + (f"  [{extra}]" if extra and not cond else ""))


if LIVE == "postgres":
    profile = {"platform": "postgres", "environment": "DEV", "agent": True, "host": "localhost", "port": 5432,
               "dbname": "postgres", "user": "postgres"}
    gold = ("CREATE SCHEMA IF NOT EXISTS GOLD;\n"
            "CREATE TABLE IF NOT EXISTS GOLD.DIM_CUSTOMER (CUSTOMER_KEY INT, NAME VARCHAR(50));\n")
    after = "CREATE TABLE IF NOT EXISTS GOLD.AFTER_FAIL (A INT);\n"
    exists_after = "SELECT COUNT(*) FROM INFORMATION_SCHEMA.TABLES WHERE UPPER(TABLE_NAME) = 'AFTER_FAIL'"
elif LIVE == "sqlserver":
    profile = {"platform": "sqlserver", "environment": "DEV", "agent": True,
               "connection_string": "Server=localhost,1433;Database=master;UID=sa;Encrypt=yes;TrustServerCertificate=yes;"
                                    f"PWD={os.environ.get('NOGAMY_LIVE_PWD', '')};"}
    gold = ("IF SCHEMA_ID('GOLD') IS NULL EXEC('CREATE SCHEMA GOLD');\nGO\n"
            "IF OBJECT_ID('GOLD.DIM_CUSTOMER') IS NULL CREATE TABLE GOLD.DIM_CUSTOMER (CUSTOMER_KEY INT, NAME VARCHAR(50));\nGO\n")
    after = "IF OBJECT_ID('GOLD.AFTER_FAIL') IS NULL CREATE TABLE GOLD.AFTER_FAIL (A INT);\n"
    exists_after = "SELECT CASE WHEN OBJECT_ID('GOLD.AFTER_FAIL') IS NULL THEN 0 ELSE 1 END"
else:
    sys.exit("set NOGAMY_LIVE=postgres or sqlserver")

d = rm.DIALECTS[rm.PLATFORM_DIALECT[profile["platform"]]]
tmp = Path(tempfile.mkdtemp())
rm.FOLDER = tmp
(tmp / "0001_create_log.sql").write_text(f"-- migration: 0001\n-- PR: test\n-- Creates the migration log.\n{rm.log_ddl(d)}\n",
                                         encoding="utf-8")
(tmp / "0002_gold_customer.sql").write_text(f"-- migration: 0002\n-- PR: test\n-- Adds GOLD.DIM_CUSTOMER.\n{gold}",
                                            encoding="utf-8")
(tmp / "0003_unknown_row.sql").write_text(
    "-- migration: 0003\n-- PR: test\n-- Adds the -99 row; safe twice.\n"
    "INSERT INTO GOLD.DIM_CUSTOMER (CUSTOMER_KEY, NAME) SELECT -99, 'unknown; none' "
    "WHERE NOT EXISTS (SELECT 1 FROM GOLD.DIM_CUSTOMER WHERE CUSTOMER_KEY = -99);\n", encoding="utf-8")
check("--check on the test files", rm.check_files() == [], str(rm.check_files()))

conn = rm.CONNECT[rm.PLATFORM_DIALECT[profile["platform"]]](profile, True)
db = rm.Db(conn, d)
code = rm.apply(profile, as_agent=True, conn=conn)
check("first run: 3 executed", code == 0 and db.executed() == {1, 2, 3}, str(db.executed()))
check("first run: user and description logged",
      db.value(f"SELECT COUNT(*) FROM {rm.LOG} WHERE EXECUTED_BY IS NOT NULL AND DESCRIPTION = 'Adds GOLD.DIM_CUSTOMER.'") == 1)
rm.apply(profile, as_agent=True, conn=conn)
rm.apply(profile, rerun=3, conn=conn)
check("second run and --rerun 3: one -99 row", db.value("SELECT COUNT(*) FROM GOLD.DIM_CUSTOMER WHERE CUSTOMER_KEY = -99") == 1)

(tmp / "0004_broken.sql").write_text("-- migration: 0004\n-- PR: test\n-- Breaks on purpose.\n"
                                     "INSERT INTO GOLD.NO_SUCH_TABLE VALUES (1);\n", encoding="utf-8")
(tmp / "0005_after.sql").write_text(f"-- migration: 0005\n-- PR: test\n-- Must not run after a failure.\n{after}",
                                    encoding="utf-8")
try:
    rm.apply(profile, as_agent=True, conn=conn)
    stopped = False
except SystemExit as e:
    stopped = "0004_broken.sql" in str(e)
err = db.value(f"SELECT ERROR_MSG FROM {rm.LOG} WHERE RUN_ORDER = 4")
check("failure: stops at 0004 with ERROR_MSG", stopped and bool(err), str(err))
check("failure: 0005 did not run", db.value(exists_after) == 0 and 5 not in db.executed())

print("FAILS:", fails)
sys.exit(1 if fails else 0)
