"""Apply pending migrations (scripts/migrations/NNNN_<what>.sql) to one database, in order — any platform.

The method is the same everywhere (scripts/README.md): numbered files, a log table MNG.MNG_MIGRATION_LOG
inside each database, pending files run lowest number first, a failure writes ERROR_MSG and stops.
Only the connection and a few SQL words differ per platform; they are the DIALECTS and CONNECT tables below.

    python tools/run_migrations.py --check                                  offline: names, numbers, headers
    python tools/run_migrations.py --profile dev --dry-run                  what would run in DEV
    python tools/run_migrations.py --profile dev [--as-agent] [--rerun N]   run the pending files
    python tools/run_migrations.py --platform snowflake --run-sheet [--from N]   no connection: a run sheet
    python tools/run_migrations.py --platform postgres --print-log-ddl      the log table, for migration 0001

Platforms: sqlserver (also Azure SQL, Synapse), fabric, snowflake, postgres, databricks.
Any other platform, or no connection at all (access level L0): --run-sheet prints every pending file and the
log statements, in order, for a person to run in any SQL tool and paste back the result.

Profiles: _private/db-profiles.json (ignored by Git) — names and addresses only, never a secret:
    {"dev": {"platform": "snowflake", "environment": "DEV", "agent": true,
             "account": "<account>", "user": "<user>", "warehouse": "<wh>", "database": "<db>",
             "authenticator": "externalbrowser"}}
Azure SQL Database has no Windows sign-in: give its profile a "connection_string" with the driver's Microsoft Entra
sign-in (Authentication=..., see nogamy-db-objects references/sqlserver.md), never a password in the file.
A secret, when one is needed, comes from the OS credential store: "keyring": {"service": "...", "username": "..."}
(pip install keyring), or from the driver's own mechanism (browser sign-in, pgpass, Windows auth).

--as-agent (the AI): only a profile with "agent": true and "environment": "DEV". Refuses before anything runs
if a pending file holds DROP: a drop is run by a person. TEST and PROD are run by people, as themselves.
Standard library only, plus the driver of the platform you connect to (imported only when used).
"""
import argparse
import json
import os
import re
import sys
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
FOLDER = ROOT / "scripts" / "migrations"
PROFILES = ROOT / "_private" / "db-profiles.json"
LOG = "MNG.MNG_MIGRATION_LOG"
NAME = re.compile(r"^(\d{4})_[A-Za-z0-9_]+\.sql$")
GO = re.compile(r"^\s*GO\s*;?\s*$", re.IGNORECASE | re.MULTILINE)

# The few words that differ. "batches": tsql = split on GO lines; sql = split on ; outside quotes,
# comments and $$ bodies (GO lines are accepted everywhere).
_INFO = ("SELECT COUNT(*) FROM INFORMATION_SCHEMA.TABLES "
         "WHERE UPPER(TABLE_SCHEMA) = 'MNG' AND UPPER(TABLE_NAME) = 'MNG_MIGRATION_LOG'")
DIALECTS = {
    "tsql": {"exists": f"SELECT CASE WHEN OBJECT_ID('{LOG}') IS NULL THEN 0 ELSE 1 END",
             "now": "CAST(SYSUTCDATETIME() AS DATETIME2(6))", "user": "SUSER_SNAME()", "batches": "tsql",
             "ts": "DATETIME2(6)", "str": "VARCHAR({n})",
             "schema": "IF SCHEMA_ID('MNG') IS NULL EXEC('CREATE SCHEMA MNG');",
             "create": f"IF OBJECT_ID('{LOG}') IS NULL\nCREATE TABLE {LOG}"},
    "snowflake": {"exists": _INFO, "now": "CURRENT_TIMESTAMP()", "user": "CURRENT_USER()", "batches": "sql",
                  "ts": "TIMESTAMP_NTZ", "str": "VARCHAR({n})", "schema": "CREATE SCHEMA IF NOT EXISTS MNG;",
                  "create": f"CREATE TABLE IF NOT EXISTS {LOG}"},
    "postgres": {"exists": _INFO, "now": "now()", "user": "current_user", "batches": "sql",
                 "ts": "TIMESTAMP", "str": "VARCHAR({n})", "schema": "CREATE SCHEMA IF NOT EXISTS MNG;",
                 "create": f"CREATE TABLE IF NOT EXISTS {LOG}"},
    "databricks": {"exists": _INFO, "now": "current_timestamp()", "user": "current_user()", "batches": "sql",
                   "ts": "TIMESTAMP", "str": "STRING", "schema": "CREATE SCHEMA IF NOT EXISTS MNG;",
                   "create": f"CREATE TABLE IF NOT EXISTS {LOG}"},
}
PLATFORM_DIALECT = {"sqlserver": "tsql", "azuresql": "tsql", "synapse": "tsql", "fabric": "tsql",
                    "snowflake": "snowflake", "postgres": "postgres", "databricks": "databricks"}


# ---------- files ----------

def migration_files():
    files = sorted((int(m.group(1)), f.name) for f in FOLDER.glob("*.sql") if (m := NAME.match(f.name)))
    return files


def read(f):
    return (FOLDER / f).read_text(encoding="utf-8-sig")


def description(f):
    """The plain sentence of the header: the first `-- ` comment that is not a tag or a divider."""
    for line in read(f).splitlines():
        s = line.strip()
        if not s:
            continue
        if not s.startswith("--"):
            break
        text = s.lstrip("-").strip()
        if text and not re.match(r"(?i)^(migration|pr|author|date)\s*:", text) and not set(text) <= {"-", "="}:
            return text[:500]
    return None


def strip_comments(sql):
    return re.sub(r"/\*.*?\*/", "", re.sub(r"--[^\n]*", "", sql), flags=re.DOTALL)


def has_drop(f):
    """DROP outside comments. Conservative: a DROP inside a string literal also counts."""
    return re.search(r"\bDROP\b", strip_comments(read(f)), re.IGNORECASE) is not None


def split_sql(text, style):
    """Statements to send one by one. tsql: GO batches. sql: ; outside quotes, comments, $tag$ bodies."""
    parts = [b for b in GO.split(text)]
    if style == "tsql":
        return [b.strip() for b in parts if strip_comments(b).strip()]
    out = []
    for part in parts:
        buf, i, n = [], 0, len(part)
        while i < n:
            c = part[i]
            if c in "'\"":  # quoted: '' and "" escape themselves
                j = i + 1
                while j < n and not (part[j] == c and (j + 1 >= n or part[j + 1] != c)):
                    j += 2 if part[j] == c else 1
                buf.append(part[i:j + 1]); i = j + 1
            elif part.startswith("--", i):
                j = part.find("\n", i); j = n if j < 0 else j
                buf.append(part[i:j]); i = j
            elif part.startswith("/*", i):
                j = part.find("*/", i + 2); j = n if j < 0 else j + 2
                buf.append(part[i:j]); i = j
            elif c == "$" and (m := re.match(r"\$[A-Za-z_]*\$", part[i:])):
                tag = m.group(0); j = part.find(tag, i + len(tag)); j = n if j < 0 else j + len(tag)
                buf.append(part[i:j]); i = j
            elif c == ";":
                out.append("".join(buf)); buf = []; i += 1
            else:
                buf.append(c); i += 1
        out.append("".join(buf))
    return [s.strip() for s in out if strip_comments(s).strip()]


def lit(v):
    return "NULL" if v is None else str(v) if isinstance(v, int) else "'" + str(v).replace("'", "''") + "'"


def check_files():
    """Offline checks; a list of problems."""
    problems, files = [], migration_files()
    for f in FOLDER.glob("*.sql"):
        if not NAME.match(f.name):
            problems.append(f"{f.name}: name is not NNNN_<what>.sql")
    nums = [n for n, _ in files]
    for n in sorted({n for n in nums if nums.count(n) > 1}):
        problems.append(f"number {n:04d} is used twice: the branch merged second renumbers")
    for n, f in files:
        if not description(f):
            problems.append(f"{f}: no description line in the header (scripts/README.md)")
    return problems


# ---------- the log, in each dialect ----------

def log_ddl(d):
    s = d["str"]
    col = lambda n: s.format(n=n) if "{n}" in s else s  # noqa: E731
    sep = "\nGO\n" if d["batches"] == "tsql" else "\n"
    return (f"{d['schema']}{sep}{d['create']}\n(\n"
            f"    RUN_ORDER      INT           NOT NULL,\n"
            f"    FILE_NAME      {col(200)}  NOT NULL,\n"
            f"    DESCRIPTION    {col(500)}  NULL,\n"
            f"    IS_EXECUTED    INT           NOT NULL,\n"
            f"    EXECUTED_AT    {d['ts']}  NULL,\n"
            f"    EXECUTED_BY    {col(200)}  NULL,\n"
            f"    REGISTERED_AT  {d['ts']}  NOT NULL,\n"
            f"    ERROR_MSG      {col(4000)} NULL\n);")


def sql_register(d, n, f):
    return (f"INSERT INTO {LOG} (RUN_ORDER, FILE_NAME, DESCRIPTION, IS_EXECUTED, REGISTERED_AT) "
            f"SELECT {n}, {lit(f)}, {lit(description(f))}, 0, {d['now']} "
            f"WHERE NOT EXISTS (SELECT 1 FROM {LOG} WHERE RUN_ORDER = {n})")


def sql_done(d, n):
    return (f"UPDATE {LOG} SET IS_EXECUTED = 1, EXECUTED_AT = {d['now']}, EXECUTED_BY = {d['user']}, "
            f"ERROR_MSG = NULL WHERE RUN_ORDER = {n}")


def sql_failed(n, err):
    return f"UPDATE {LOG} SET IS_EXECUTED = 0, ERROR_MSG = {lit(str(err)[:4000])} WHERE RUN_ORDER = {n}"


# ---------- connections (driver imported only when used) ----------

def secret(p):
    k = p.get("keyring")
    if not k:
        return None
    import keyring  # pip install keyring
    return keyring.get_password(k["service"], k["username"])


def connect_tsql(p, as_agent):
    import mssql_python  # pip install mssql-python
    if p.get("platform") == "fabric":
        if as_agent:  # the Fabric pack's allow list (tools/fabric) refuses anything not on it
            sys.path.insert(0, str(ROOT / "tools" / "fabric"))
            from fabric_client import sql_connect
            return sql_connect(p["server"], p.get("database", "WH_DWH"))
        import struct
        from azure.identity import InteractiveBrowserCredential, TokenCachePersistenceOptions
        tenant = p.get("tenant_id")
        if not tenant:
            try:
                tenant = json.loads((ROOT / "_private" / "fabric_agent.json").read_text(encoding="utf-8"))["tenant_id"]
            except (OSError, KeyError, ValueError):
                sys.exit("no tenant: set tenant_id in the profile or in _private/fabric_agent.json")
        token = InteractiveBrowserCredential(
            tenant_id=tenant, cache_persistence_options=TokenCachePersistenceOptions(name="nogamy-migrate")
        ).get_token("https://database.windows.net/.default").token.encode("utf-16-le")
        return mssql_python.connect(f"Server={p['server']},1433;Database={p.get('database', 'WH_DWH')};Encrypt=yes;",
                                    autocommit=True, attrs_before={1256: struct.pack(f"<I{len(token)}s", len(token), token)})
    cs = p.get("connection_string") or f"Server={p['server']};Database={p['database']};Encrypt=yes;Trusted_Connection=yes;"
    pw = secret(p)
    return mssql_python.connect(cs + (f"Pwd={pw};" if pw else ""), autocommit=True)


def connect_snowflake(p, as_agent):
    import snowflake.connector  # pip install snowflake-connector-python
    kw = {k: p[k] for k in ("account", "user", "warehouse", "database", "schema", "role") if p.get(k)}
    pw = secret(p)
    kw.update({"password": pw} if pw else {"authenticator": p.get("authenticator", "externalbrowser")})
    return snowflake.connector.connect(**kw)


def connect_postgres(p, as_agent):
    import psycopg  # pip install psycopg[binary]
    kw = {k: p[k] for k in ("host", "port", "dbname", "user") if p.get(k)}
    pw = secret(p)
    conn = psycopg.connect(**kw, **({"password": pw} if pw else {}))  # else ~/.pgpass or PGPASSWORD
    conn.autocommit = True
    return conn


def connect_databricks(p, as_agent):
    from databricks import sql  # pip install databricks-sql-connector
    kw = {"server_hostname": p["server_hostname"], "http_path": p["http_path"]}
    pw = secret(p)
    kw.update({"access_token": pw} if pw else {"auth_type": "databricks-oauth"})
    conn = sql.connect(**kw)
    if p.get("catalog"):
        conn.cursor().execute(f"USE CATALOG {p['catalog']}")
    return conn


CONNECT = {"tsql": connect_tsql, "snowflake": connect_snowflake, "postgres": connect_postgres,
           "databricks": connect_databricks}


class Db:
    def __init__(self, conn, d):
        self.conn, self.d, self.cur = conn, d, conn.cursor()

    def run(self, sql):
        self.cur.execute(sql)
        try:
            while self.cur.nextset():
                pass
        except Exception:  # drivers without multiple result sets
            pass

    def value(self, sql):
        self.cur.execute(sql)
        return self.cur.fetchone()[0]

    def log_exists(self):
        return bool(self.value(self.d["exists"]))

    def executed(self):
        if not self.log_exists():
            return set()
        self.cur.execute(f"SELECT RUN_ORDER FROM {LOG} WHERE IS_EXECUTED = 1")
        return {int(r[0]) for r in self.cur.fetchall()}

    def register_all(self, files):
        """A row with IS_EXECUTED = 0 for every file not in the log yet."""
        self.cur.execute(f"SELECT RUN_ORDER FROM {LOG}")
        known = {int(r[0]) for r in self.cur.fetchall()}
        for n, f in files:
            if n not in known:
                self.run(f"INSERT INTO {LOG} (RUN_ORDER, FILE_NAME, DESCRIPTION, IS_EXECUTED, REGISTERED_AT) "
                         f"VALUES ({n}, {lit(f)}, {lit(description(f))}, 0, {self.d['now']})")


# ---------- modes ----------

def run_sheet(d, files, first):
    pending = [(n, f) for n, f in files if n >= first]
    lines = [f"# Run sheet — migrations from {first:04d} ({date.today().isoformat()})", "",
             "Run each step in order, in the SQL tool of the environment, as yourself.",
             "Stop at the first error and paste it back. Paste back the result of step 0 and of the last step.", "",
             "## Step 0 — what this environment already has", "", "```sql",
             f"SELECT RUN_ORDER, FILE_NAME, IS_EXECUTED FROM {LOG} ORDER BY RUN_ORDER;", "```",
             f"Expected: every number below {first:04d} with IS_EXECUTED = 1. A higher number already = 1 → skip it below.",
             "(No such table yet → migration 0001 creates it; start from 0001.)", ""]
    for n, f in pending:
        lines += [f"## Step {n:04d} — {f}", "", description(f) or "", "", "```sql", read(f).strip(), "```", "",
                  "Then, in the same environment:", "", "```sql",
                  sql_register(d, n, f) + ";", sql_done(d, n) + ";", "```",
                  "Expected: no error; the UPDATE changes 1 row.", ""]
    lines += ["## Last step — check", "", "```sql",
              f"SELECT RUN_ORDER, FILE_NAME, IS_EXECUTED, EXECUTED_AT FROM {LOG} WHERE RUN_ORDER >= {first} ORDER BY RUN_ORDER;",
              "```", f"Expected: {len(pending)} rows, all IS_EXECUTED = 1.", ""]
    return "\n".join(lines)


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--profile", help="a profile in _private/db-profiles.json")
    ap.add_argument("--platform", help="for --run-sheet / --print-log-ddl without a profile: " + ", ".join(PLATFORM_DIALECT))
    ap.add_argument("--check", action="store_true", help="offline checks of scripts/migrations/")
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--rerun", type=int, help="DEV only: run N again after it was rewritten on a branch not merged yet")
    ap.add_argument("--as-agent", action="store_true", help="the AI: DEV profile with agent: true; refuses DROP")
    ap.add_argument("--run-sheet", action="store_true", help="no connection: write a run sheet for a person")
    ap.add_argument("--from", dest="first", type=int, default=1, help="--run-sheet: first migration number")
    ap.add_argument("--out", help="--run-sheet: file to write (default: print)")
    ap.add_argument("--print-log-ddl", action="store_true", help="the log table DDL, for migration 0001")
    a = ap.parse_args()

    if a.check:
        probs = check_files()
        for p in probs:
            print(p)
        print("ok" if not probs else f"{len(probs)} problems")
        return 1 if probs else 0

    profile = {}
    if a.profile:
        try:
            profile = json.loads(PROFILES.read_text(encoding="utf-8"))[a.profile]
        except (OSError, ValueError, KeyError):
            sys.exit(f"no profile '{a.profile}' in {PROFILES.relative_to(ROOT).as_posix()} (see the top of this file)")
    platform = (a.platform or profile.get("platform") or "").lower()
    if platform not in PLATFORM_DIALECT:
        sys.exit(f"platform '{platform or '?'}' has no dialect here ({', '.join(PLATFORM_DIALECT)}). "
                 "Use --run-sheet with the closest one and check the log statements, or nogamy-feedback to add it.")
    d = DIALECTS[PLATFORM_DIALECT[platform]]

    if a.print_log_ddl:
        print(log_ddl(d))
        return 0

    files = migration_files()
    if len({n for n, _ in files}) != len(files):
        sys.exit("two migration files share a number: fix before running (--check)")

    if a.run_sheet:
        text = run_sheet(d, files, a.first)
        if a.out:
            Path(a.out).parent.mkdir(parents=True, exist_ok=True)
            Path(a.out).write_text(text, encoding="utf-8")
            print(f"wrote {a.out}")
        else:
            print(text)
        return 0

    if not a.profile:
        sys.exit("--profile is needed to connect (or use --run-sheet)")
    profile = {**profile, "platform": platform}
    return apply(profile, dry_run=a.dry_run, rerun=a.rerun, as_agent=a.as_agent)


def apply(profile, dry_run=False, rerun=None, as_agent=False, conn=None):
    """Connect with the profile (or use conn) and run the pending migrations. Used by main and by pack wrappers."""
    platform = str(profile.get("platform", "")).lower()
    d = DIALECTS[PLATFORM_DIALECT[platform]]
    files = migration_files()
    if len({n for n, _ in files}) != len(files):
        sys.exit("two migration files share a number: fix before running (--check)")
    if as_agent and not (profile.get("agent") is True and str(profile.get("environment", "")).upper() == "DEV"):
        sys.exit("refusing --as-agent: the profile is not marked agent: true with environment: DEV")
    if rerun and str(profile.get("environment", "")).upper() != "DEV":
        sys.exit("refusing --rerun: DEV only")

    db = Db(conn or CONNECT[PLATFORM_DIALECT[platform]](profile, as_agent), d)
    done = db.executed() - ({rerun} if rerun else set())
    pending = [(n, f) for n, f in files if n not in done]
    print(f"executed: {len(done)}  pending: {len(pending)}")
    for _, f in pending:
        print(f"  {f}")
    if as_agent:
        drops = [f for _, f in pending if has_drop(f)]
        if drops:
            sys.exit("refusing --as-agent: DROP in " + ", ".join(drops) + ". A person runs these, without --as-agent.")
    if dry_run or not pending:
        return 0

    if db.log_exists():
        db.register_all(files)
    for n, f in pending:
        try:
            for stmt in split_sql(read(f), d["batches"]):
                db.run(stmt)
        except Exception as e:
            if db.log_exists():
                db.register_all(files)
                db.run(sql_failed(n, e))
            sys.exit(f"FAILED: {f}\n{e}")
        db.register_all(files)  # 0001 creates the log: register right after it
        db.run(sql_done(d, n))
        print(f"executed: {f}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
