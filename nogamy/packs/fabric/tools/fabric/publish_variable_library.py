"""Publish a Variable library from the repo to an allowed workspace. Creates the item when it does not exist yet.

The repo folder is the source: variables.json, settings.json and valueSets/*.json replace the definition in Fabric.
The active value set is not part of the definition: it stays as set in each workspace.

Usage: python tools/fabric/publish_variable_library.py <workspace> <path to X.VariableLibrary folder> [--as-user]
"""
import base64
import glob
import os
import sys

from fabric_client import call, session, workspace_id

ws_name, folder = [a for a in sys.argv[1:] if a != "--as-user"][:2]
name = os.path.basename(os.path.normpath(folder)).removesuffix(".VariableLibrary")
parts = []
for f in glob.glob(os.path.join(folder, "**", "*.json"), recursive=True):
    payload = base64.b64encode(open(f, "rb").read()).decode()
    parts.append({"path": os.path.relpath(f, folder).replace(os.sep, "/"), "payloadType": "InlineBase64", "payload": payload})

s = session(as_user="--as-user" in sys.argv)
ws = workspace_id(ws_name)
items = call(s, "GET", f"/workspaces/{ws}/items?type=VariableLibrary")["value"]
item = next((i for i in items if i["displayName"] == name), None)
if item:
    call(s, "POST", f"/workspaces/{ws}/items/{item['id']}/updateDefinition", json={"definition": {"parts": parts}})
else:
    call(s, "POST", f"/workspaces/{ws}/items", json={"displayName": name, "type": "VariableLibrary", "definition": {"parts": parts}})
print(f"published {name} to {ws_name}")
