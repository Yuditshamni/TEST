"""Fabric access for the AI agent, as the agent's own identity (service principal).

- Identity: client id + tenant id from _private/fabric_agent.json, secret from Windows Credential Manager
  (keyring service name in the same file). Nothing secret lives in the repo.
- Allow list: only workspaces and SQL servers listed in the config. Anything else is refused here,
  and Fabric itself refuses it too because the identity has no role there.
"""
import json
import os
import struct
import sys
import time

import keyring
import requests
from azure.identity import ClientSecretCredential

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
CONFIG = json.load(open(os.path.join(ROOT, "_private", "fabric_agent.json"), encoding="utf-8"))
API = "https://api.fabric.microsoft.com/v1"
FABRIC_SCOPE = "https://api.fabric.microsoft.com/.default"
SQL_SCOPE = "https://database.windows.net/.default"


def credential():
    secret = keyring.get_password(CONFIG["keyring_service"], "secret")
    if not secret:
        sys.exit(f"agent secret not found in Windows Credential Manager (service '{CONFIG['keyring_service']}', user 'secret'; see tools/README.md)")
    return ClientSecretCredential(CONFIG["tenant_id"], CONFIG["client_id"], secret)


def user_credential():
    """The developer's own sign-in (browser once, then cached). Needed to save a pipeline that uses a
    connection shared with the developer but not with the agent (e.g. a source system through the gateway)."""
    from azure.identity import AuthenticationRecord, InteractiveBrowserCredential, TokenCachePersistenceOptions

    opts = TokenCachePersistenceOptions(name="nogamy_fabric_user")
    rec_path = os.path.join(ROOT, "_private", "fabric_user_auth.json")
    if os.path.exists(rec_path):
        rec = AuthenticationRecord.deserialize(open(rec_path, encoding="utf-8").read())
        return InteractiveBrowserCredential(tenant_id=CONFIG["tenant_id"], cache_persistence_options=opts,
                                            authentication_record=rec)
    cred = InteractiveBrowserCredential(tenant_id=CONFIG["tenant_id"], cache_persistence_options=opts)
    open(rec_path, "w", encoding="utf-8").write(cred.authenticate(scopes=[FABRIC_SCOPE]).serialize())
    return cred


def session(as_user=False):
    s = requests.Session()
    cred = user_credential() if as_user else credential()
    s.headers["Authorization"] = "Bearer " + cred.get_token(FABRIC_SCOPE).token
    return s


def workspace_id(name):
    if name not in CONFIG["workspaces"]:
        sys.exit(f"refusing: workspace '{name}' is not on the allow list")
    return CONFIG["workspaces"][name]


def call(s, method, path, **kw):
    """REST call; waits for long running operations (202 + Location)."""
    r = s.request(method, API + path, **kw)
    if r.status_code == 202 and "Location" in r.headers:
        loc = r.headers["Location"]
        while True:
            time.sleep(int(r.headers.get("Retry-After", 3)))
            r = s.get(loc)
            status = r.json().get("status")
            if status in ("Succeeded", "Failed"):
                if status == "Failed":
                    sys.exit(f"operation failed: {r.text}")
                res = s.get(loc + "/result")
                return res.json() if res.content else {}
    if not r.ok:
        sys.exit(f"{method} {path} -> {r.status_code}: {r.text}")
    return r.json() if r.content else {}


def sql_connect(server, database):
    import mssql_python

    if server.lower() not in CONFIG["sql_servers"]:
        sys.exit(f"refusing: SQL server {server} is not on the allow list")
    tok = credential().get_token(SQL_SCOPE).token.encode("utf-16-le")
    attrs = {1256: struct.pack(f"<I{len(tok)}s", len(tok), tok)}  # SQL_COPT_SS_ACCESS_TOKEN
    return mssql_python.connect(f"Server={server},1433;Database={database};Encrypt=yes;",
                                autocommit=True, attrs_before=attrs)
