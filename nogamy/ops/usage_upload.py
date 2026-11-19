"""Upload new usage events to the core repo, branch `usage-data`. Called by core_update.py check (daily).

No server, no secret: the developer's own `gh` access writes one small file per upload through the
GitHub contents API. The weekly curator (core repo) reads that branch and builds the report.
Events are metadata only (nogamy/hooks/nogamy_telemetry.py). Telemetry: off in PROJECT.md → nothing is sent.
"""
import base64
import hashlib
import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "hooks"))
import nogamy_telemetry as tel  # noqa: E402

BRANCH = "usage-data"
OFFSET = tel.HOME / "upload-offset.json"
MAX_EVENTS = 5000


def upload(core_repo):
    if not tel.LOG.exists():
        return 0
    try:
        off = json.loads(OFFSET.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        off = {}
    size = tel.LOG.stat().st_size
    start = off.get("bytes", 0) if off.get("inode") == _id(tel.LOG) and off.get("bytes", 0) <= size else 0
    with tel.LOG.open("rb") as f:
        f.seek(start)
        chunk = f.read()
    lines = [x for x in chunk.decode("utf-8", errors="ignore").splitlines() if x.strip()][:MAX_EVENTS]
    if not lines:
        return 0
    first = json.loads(lines[0])
    who = hashlib.sha256(first.get("user", "unknown").encode()).hexdigest()[:8]
    now = datetime.now(timezone.utc)
    path = f"usage/{now:%Y/%m/%d}/{first.get('project', 'unknown')}-{who}-{now:%H%M%S}.jsonl"
    content = base64.b64encode(("\n".join(lines) + "\n").encode()).decode()
    r = subprocess.run(["gh", "api", "-X", "PUT", f"repos/{core_repo}/contents/{path}",
                        "-f", f"message=usage: {len(lines)} events", "-f", f"content={content}", "-f", f"branch={BRANCH}"],
                       capture_output=True, text=True)
    if r.returncode != 0:
        raise RuntimeError(r.stderr.strip()[:200])
    OFFSET.write_text(json.dumps({"inode": _id(tel.LOG), "bytes": start + len(chunk)}), encoding="utf-8")
    return len(lines)


def _id(p):
    st = p.stat()
    return f"{st.st_ctime_ns}"


if __name__ == "__main__":
    print(upload(sys.argv[1]))
