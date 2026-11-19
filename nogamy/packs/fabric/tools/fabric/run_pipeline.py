"""Run a data pipeline in an allowed workspace and wait for the result.

Usage: python tools/fabric/run_pipeline.py <workspace> <pipeline name> [NAME=value ...]
  NAME=value   pipeline parameters, e.g. P_Source_Group=SALES
Runs as the agent. Not as the developer: a run started by API with the developer's browser token
fails to resolve gateway connections (DMTS_EntityNotFoundOrUnauthorized).
Exit code 1 when the run fails. A failed run prints every failed activity with its error,
including activities whose failure the pipeline swallowed (status Completed but an activity failed).
"""
import sys
import time

from fabric_client import API, call, session, workspace_id

ws_name, pipeline = sys.argv[1:3]
params = dict(a.split("=", 1) for a in sys.argv[3:])
s = session()
ws = workspace_id(ws_name)
items = call(s, "GET", f"/workspaces/{ws}/items?type=DataPipeline")["value"]
item = next((i for i in items if i["displayName"] == pipeline), None)
if not item:
    sys.exit(f"pipeline '{pipeline}' not found in {ws_name}")

r = s.post(f"{API}/workspaces/{ws}/items/{item['id']}/jobs/instances?jobType=Pipeline",
           json={"executionData": {"parameters": params}})
if r.status_code != 202:
    sys.exit(f"run request failed: {r.status_code} {r.text}")
loc = r.headers["Location"]
while True:
    job = s.get(loc).json()
    if job["status"] not in ("NotStarted", "InProgress"):
        break
    time.sleep(5)

print("status:", job["status"], "| start:", job.get("startTimeUtc"), "| end:", job.get("endTimeUtc"))
runs = s.post(f"{API}/workspaces/{ws}/datapipelines/pipelineruns/{job['id']}/queryactivityruns",
              json={"filters": [], "orderBy": [{"orderBy": "ActivityRunStart", "order": "ASC"}],
                    "lastUpdatedAfter": job["startTimeUtc"] + "Z", "lastUpdatedBefore": "2100-01-01T00:00:00Z"})
for a in runs.json().get("value", []) if runs.ok else []:
    if a.get("status") == "Failed":
        print("failed activity:", a.get("activityName"), "|", (a.get("error") or {}).get("message"))
if job["status"] != "Completed":
    print("error:", job.get("failureReason"))
    sys.exit(1)
