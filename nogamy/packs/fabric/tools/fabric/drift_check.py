"""Compare the repo with what is live in an allowed workspace. Read-only.

Checks every X.DataPipeline/pipeline-content.json and every .sql under X.Warehouse/ in the given folder:
  pipelines: JSON equal to the live definition, after replacing connection placeholders as publish_pipeline.py does
  variable libraries: variables.json and valueSets equal to the live definition
  procedures, views, functions: code equal to OBJECT_DEFINITION (comments and whitespace ignored)
  tables: column names, types and nullability equal to sys.columns
Also lists objects that are live but have no file in the repo.

Usage: python tools/fabric/drift_check.py <workspace> <repo folder> <warehouse server>
Exit code 1 when something differs.
"""
import base64
import glob
import json
import os
import re
import sys

from fabric_client import CONFIG, call, session, sql_connect, workspace_id

ws_name, root, server = sys.argv[1:4]
norm = lambda t: re.sub(r"\s+", " ", re.sub(r"--[^\n]*", "", t)).strip().rstrip(";").lower()
diffs = 0


def report(name, same, detail=""):
    global diffs
    diffs += not same
    print(f"{'SYNCED' if same else 'DIFF  '}  {name}{detail}")


s = session()
ws = workspace_id(ws_name)
live_items = call(s, "GET", f"/workspaces/{ws}/items")["value"]

# pipelines
repo_pipelines = set()
for f in glob.glob(os.path.join(root, "**", "*.DataPipeline", "pipeline-content.json"), recursive=True):
    name = os.path.basename(os.path.dirname(f)).removesuffix(".DataPipeline")
    repo_pipelines.add(name)
    item = next((i for i in live_items if i["type"] == "DataPipeline" and i["displayName"] == name), None)
    if not item:
        report(f"pipeline {name}", False, " (missing in Fabric)")
        continue
    parts = call(s, "POST", f"/workspaces/{ws}/items/{item['id']}/getDefinition")["definition"]["parts"]
    live = json.loads(base64.b64decode(next(p["payload"] for p in parts if p["path"] == "pipeline-content.json")))
    content = open(f, encoding="utf-8").read()
    for placeholder, conn_id in CONFIG.get("connections", {}).get(ws_name, {}).items():
        content = content.replace(placeholder, conn_id)
    report(f"pipeline {name}", live == json.loads(content))

# variable libraries
repo_libraries = set()
for d in glob.glob(os.path.join(root, "**", "*.VariableLibrary"), recursive=True):
    name = os.path.basename(d).removesuffix(".VariableLibrary")
    repo_libraries.add(name)
    item = next((i for i in live_items if i["type"] == "VariableLibrary" and i["displayName"] == name), None)
    if not item:
        report(f"variable library {name}", False, " (missing in Fabric)")
        continue
    parts = call(s, "POST", f"/workspaces/{ws}/items/{item['id']}/getDefinition")["definition"]["parts"]
    live = {p["path"]: json.loads(base64.b64decode(p["payload"])) for p in parts if p["path"].endswith(".json") and p["path"] != "settings.json"}
    repo = {os.path.relpath(f, d).replace(os.sep, "/"): json.load(open(f, encoding="utf-8"))
            for f in glob.glob(os.path.join(d, "**", "*.json"), recursive=True) if os.path.basename(f) != "settings.json"}
    report(f"variable library {name}", live == repo)

# warehouses
repo_objects = set()
for wh_dir in glob.glob(os.path.join(root, "**", "*.Warehouse"), recursive=True):
    db = os.path.basename(wh_dir).removesuffix(".Warehouse")
    cur = sql_connect(server, db).cursor()
    for f in glob.glob(os.path.join(wh_dir, "**", "*.sql"), recursive=True):
        code = open(f, encoding="utf-8").read()
        m = re.search(r"CREATE\s+(TABLE|PROCEDURE|PROC|VIEW|FUNCTION)\s+([\w\[\]\.]+)", code, re.I)
        if not m:
            continue
        kind, obj = m.group(1).upper(), m.group(2).replace("[", "").replace("]", "")
        repo_objects.add(obj.split(".")[-1].lower())
        if kind == "TABLE":
            cur.execute("""SELECT c.name, TYPE_NAME(c.user_type_id), c.max_length, c.precision, c.scale, c.is_nullable
                           FROM sys.columns c WHERE c.object_id = OBJECT_ID(?) ORDER BY c.column_id""", obj)
            fmt = lambda t, ml, p, sc: t + {"varchar": f"({ml})", "char": f"({ml})", "decimal": f"({p}, {sc})",
                                           "datetime2": f"({sc})"}.get(t, "")
            live = [f"{r[0]} {fmt(*r[1:5])} {'null' if r[5] else 'not null'}".lower() for r in cur.fetchall()]
            repo = [re.sub(r"\s+", " ", l.strip().rstrip(",")).lower() for l in code.splitlines()
                    if re.match(r"\s+\w+\s+\w+", l)]
            report(f"table {obj}", live == repo, "" if live == repo else f"\n    live: {live}\n    repo: {repo}")
        else:
            cur.execute("SELECT OBJECT_DEFINITION(OBJECT_ID(?))", obj)
            live = cur.fetchone()[0]
            report(f"{kind.lower()} {obj}", bool(live) and norm(live) == norm(code), "" if live else " (missing in Fabric)")
    cur.execute("SELECT name, type_desc FROM sys.objects WHERE is_ms_shipped = 0 AND type IN ('U','V','P','FN','IF','TF')")
    extra = [f"{n} ({t})" for n, t in cur.fetchall() if n.lower() not in repo_objects]
    if extra:
        print(f"\nIn {db} but not in the repo:", ", ".join(sorted(extra)))

untracked = [i["displayName"] for i in live_items if i["type"] == "DataPipeline" and i["displayName"] not in repo_pipelines]
if untracked:
    print(f"Pipelines in {ws_name} but not in the repo:", ", ".join(sorted(untracked)))

print("\nRESULT:", "repo matches Fabric for every file it has" if not diffs else f"{diffs} difference(s)")
sys.exit(1 if diffs else 0)
