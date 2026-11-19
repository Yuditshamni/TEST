"""Fabric: apply pending migrations to one warehouse — the Fabric entry to the generic runner tools/run_migrations.py.

The method, the log (MNG.MNG_MIGRATION_LOG), the order, the DROP refusal and --rerun are the generic runner's.
This file only keeps the Fabric command line and its two sign-ins:
- A person, as that person (browser sign-in, tenant from --tenant or _private/fabric_agent.json). The only way to TEST and PROD.
- --as-agent: the agent, as the AI identity, through the allow list in tools/fabric (the DEV workspace only).

Usage:
  python tools/migrate/run_migrations.py <sql endpoint> [--warehouse WH_DWH] [--dry-run] [--as-agent] [--rerun N]
Without a connection (a run sheet for a person): python tools/run_migrations.py --platform fabric --run-sheet
Requirements: pip install azure-identity mssql-python
"""
import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools"))
import run_migrations as core  # noqa: E402  (tools/run_migrations.py)

ap = argparse.ArgumentParser()
ap.add_argument("server")
ap.add_argument("--warehouse", default="WH_DWH")
ap.add_argument("--dry-run", action="store_true")
ap.add_argument("--rerun", type=int, help="DEV workspace only: run this migration again although IS_EXECUTED = 1, "
                                         "only for a migration of a branch not merged yet, after it was rewritten")
ap.add_argument("--tenant", help="tenant id; default: tenant_id in _private/fabric_agent.json")
ap.add_argument("--as-agent", action="store_true",
                help="run as the AI identity (DEV workspace only, allow list); refuses any pending file with DROP")
a = ap.parse_args()

profile = {"platform": "fabric", "server": a.server, "database": a.warehouse, "tenant_id": a.tenant,
           # the allow list in tools/fabric is the guard for the agent; a person states DEV by using --rerun
           "agent": a.as_agent, "environment": "DEV" if (a.as_agent or a.rerun) else ""}
sys.exit(core.apply(profile, dry_run=a.dry_run, rerun=a.rerun, as_agent=a.as_agent))
