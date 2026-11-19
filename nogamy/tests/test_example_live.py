"""The worked example (nogamy/examples/acme-sales/) end to end on a real SQL Server (core CI service container).

    NOGAMY_LIVE_PWD=... python nogamy/tests/test_example_live.py

In its own database: the example's migrations by tools/run_migrations.py (as the agent, DEV profile), the load
procedure twice (same counts: idempotent), then the example's QA file: every check PASS, after each load.
"""
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
EX = ROOT / "nogamy/examples/acme-sales"
sys.path.insert(0, str(ROOT / "tools"))
import run_migrations as rm  # noqa: E402

DB = "ACME_EXAMPLE"
CS = "Server=localhost,1433;UID=sa;Encrypt=yes;TrustServerCertificate=yes;PWD=" + os.environ.get("NOGAMY_LIVE_PWD", "") + ";"
fails = 0


def check(title, cond, extra=""):
    global fails
    fails += not cond
    print(("PASS " if cond else "FAIL ") + f"[example] {title}" + (f"  [{extra}]" if extra and not cond else ""))


def rows(conn, sql):
    cur = conn.cursor()
    cur.execute(sql)
    out = cur.fetchall() if cur.description else []
    cols = [c[0] for c in cur.description] if cur.description else []
    return [dict(zip(cols, r)) for r in out]


master = rm.CONNECT["tsql"]({"platform": "sqlserver", "connection_string": CS + "Database=master;"}, False)
master.cursor().execute(f"IF DB_ID('{DB}') IS NULL CREATE DATABASE {DB};")

profile = {"platform": "sqlserver", "environment": "DEV", "agent": True, "connection_string": CS + f"Database={DB};"}
rm.FOLDER = EX / "scripts/migrations"
check("--check on the example migrations", rm.check_files() == [], str(rm.check_files()))
conn = rm.CONNECT["tsql"](profile, True)
code = rm.apply(profile, as_agent=True, conn=conn)
db = rm.Db(conn, rm.DIALECTS["tsql"])
n = len(rm.migration_files())
check(f"migrations: all {n} executed and logged", code == 0 and db.executed() == {k for k, _ in rm.migration_files()},
      str(db.executed()))
rm.apply(profile, as_agent=True, conn=conn)
check("migrations: a second run changes nothing", db.value("SELECT COUNT(*) FROM BRONZE.BRONZE_ERP_CUSTOMERS") == 8,
      str(db.value("SELECT COUNT(*) FROM BRONZE.BRONZE_ERP_CUSTOMERS")))

qa = (EX / "qa/data/SALES_DIM_CUSTOMER.sql").read_text(encoding="utf-8")
counts = []
for run in (1, 2):
    r = rows(conn, "EXEC SILVER.SP_SALES_DIM_CUSTOMER;")
    counts.append(r[0] if r else {})
    res = rows(conn, qa)
    bad = [x for x in res if str(x.get("RESULT")) != "PASS"]
    check(f"load {run}: the procedure returns staging and gold counts", bool(r), str(r))
    check(f"load {run}: every QA check PASS ({len(res)} checks)", len(res) >= 7 and not bad, str(bad or res))
check("load twice -> the same counts (idempotent)", counts[0] == counts[1] and counts[0], str(counts))
check("gold: 7 customers + the -99 row", db.value("SELECT COUNT(*) FROM GOLD.SALES_DIM_CUSTOMER") == 8)

print("FAILS:", fails)
sys.exit(1 if fails else 0)
