"""Run T-SQL on an allowed warehouse as the agent identity.

Usage:
  python tools/fabric/wh_sql.py <server> <database> "SELECT ..."
  python tools/fabric/wh_sql.py <server> <database> @path/to/file.sql     (whole file as one batch)
"""
import sys

from fabric_client import sql_connect

server, database, sql = sys.argv[1:4]
if sql.startswith("@"):
    sql = open(sql[1:], encoding="utf-8").read()

cur = sql_connect(server, database).cursor()
cur.execute(sql)
while True:
    if cur.description:
        cols = [c[0] for c in cur.description]
        rows = cur.fetchall()
        print(" | ".join(cols))
        for r in rows:
            print(" | ".join("" if v is None else str(v) for v in r))
        print(f"({len(rows)} rows)\n")
    if not cur.nextset():
        break
