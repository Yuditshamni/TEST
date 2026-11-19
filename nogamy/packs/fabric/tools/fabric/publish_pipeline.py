"""Publish a pipeline definition from the repo to an allowed workspace.

The repo file is the source: whatever is in pipeline-content.json replaces the definition in Fabric.
A pipeline missing in the workspace is created, in the workspace folder that mirrors the repo
(fabric/data/pipelines/<project>/03_gold/X -> pipelines/<project>/03_gold; a TRY_ pipeline -> pipelines/TRY). Missing folders are created.

Usage: python tools/fabric/publish_pipeline.py <workspace> <path to X.DataPipeline folder> [--as-user]
  --as-user  save as the developer (browser sign-in). Needed when the pipeline uses a connection shared
             with the developer but not with the agent: Fabric refuses the save otherwise
             ("User does not have access to the connection used in the Pipeline").

Connection placeholders (__SOURCE_SYSTEM_CONNECTION__ ...) are replaced from "connections" in
_private/fabric_agent.json, per workspace. A placeholder with no value there stops the publish.
"""
import base64
import json
import os
import re
import sys

from fabric_client import CONFIG, ROOT, call, session, workspace_id

ws_name, folder = [a for a in sys.argv[1:] if a != "--as-user"][:2]
name = os.path.basename(os.path.normpath(folder)).removesuffix(".DataPipeline")
content = open(os.path.join(folder, "pipeline-content.json"), encoding="utf-8").read()
json.loads(content)  # fail early on broken JSON

for placeholder, conn_id in CONFIG.get("connections", {}).get(ws_name, {}).items():
    content = content.replace(placeholder, conn_id)
missing = sorted(set(re.findall(r"__[A-Z_]+_CONNECTION__", content)))
if missing:
    sys.exit(f"no connection ID for {missing} in _private/fabric_agent.json connections.{ws_name}")

s = session(as_user="--as-user" in sys.argv)
ws = workspace_id(ws_name)
part = {"path": "pipeline-content.json", "payloadType": "InlineBase64",
        "payload": base64.b64encode(content.encode("utf-8")).decode()}
items = call(s, "GET", f"/workspaces/{ws}/items?type=DataPipeline")["value"]
item = next((i for i in items if i["displayName"] == name), None)
if item:
    call(s, "POST", f"/workspaces/{ws}/items/{item['id']}/updateDefinition", json={"definition": {"parts": [part]}})
    print(f"published {name} to {ws_name}")
    sys.exit(0)


def folder_id(path):
    """ID of a workspace folder path like pipelines/<project>/03_gold; creates the missing levels."""
    folders = call(s, "GET", f"/workspaces/{ws}/folders")["value"]
    parent = None
    for part_name in path.split("/"):
        f = next((f for f in folders if f["displayName"] == part_name and f.get("parentFolderId") == parent), None)
        if not f:
            body = {"displayName": part_name, **({"parentFolderId": parent} if parent else {})}
            f = call(s, "POST", f"/workspaces/{ws}/folders", json=body)
            folders.append(f)
        parent = f["id"]
    return parent


rel = os.path.relpath(os.path.dirname(os.path.abspath(os.path.normpath(folder))), os.path.join(ROOT, "fabric", "data"))
ws_folder = "pipelines/TRY" if name.startswith("TRY_") else rel.replace(os.sep, "/")
call(s, "POST", f"/workspaces/{ws}/items", json={"displayName": name, "type": "DataPipeline",
                                                 "folderId": folder_id(ws_folder), "definition": {"parts": [part]}})
print(f"created {name} in {ws_name}/{ws_folder}")
