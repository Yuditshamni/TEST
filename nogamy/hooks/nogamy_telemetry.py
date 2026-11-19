"""Usage events for the Nogamy dashboard (nogamy/docs/telemetry.md). Standard library only.

Never sends prompts, file contents, data, or project paths. Only: event, skill, project id,
core version, agent, session, user, timestamp, and for core events the core path.

emit(event) appends to ~/.nogamy/usage.jsonl (always, unless Telemetry: off) and to a send queue.
A detached `python nogamy_telemetry.py --flush` posts the queue to NOGAMY_TELEMETRY_URL
(env var; optional header NOGAMY_TELEMETRY_AUTH), so the agent never waits for the network.
"""
import hashlib
import json
import os
import re
import subprocess
import sys
import time
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

HOME = Path(os.environ.get("NOGAMY_HOME", Path.home() / ".nogamy"))
LOG = HOME / "usage.jsonl"
QUEUE = HOME / "queue.jsonl"
LOCK = HOME / "flush.lock"
MAX_LOG_BYTES = 5_000_000


def repo_root():
    p = Path.cwd()
    for d in (p, *p.parents):
        if (d / "AGENTS.md").exists() and (d / "nogamy").is_dir():
            return d
    return p


def project_settings(root):
    """(project id, telemetry mode) from PROJECT.md."""
    pid, mode = "unknown", "on"
    f = Path(root, "PROJECT.md")
    if f.exists():
        for line in f.read_text(encoding="utf-8").splitlines():
            m = re.match(r"\s*-\s*Project id\s*:\s*`?([\w.-]+)", line)
            if m and "<" not in line.split(":", 1)[1].split("(")[0]:
                pid = m.group(1)
            m = re.match(r"\s*-\s*Telemetry\s*:\s*(on|anonymous|off)\b", line, re.I)
            if m:
                mode = m.group(1).lower()
    return pid, os.environ.get("NOGAMY_TELEMETRY_MODE", mode).lower()


def git_user(root):
    try:
        return subprocess.run(["git", "config", "user.email"], cwd=root, capture_output=True,
                              text=True, timeout=2).stdout.strip() or "unknown"
    except (OSError, subprocess.SubprocessError):
        return "unknown"


def core_version(root):
    f = Path(root, ".core-version")
    return f.read_text(encoding="utf-8").strip() if f.exists() else "none"


def agent_name(d):
    """Claude Code sets CLAUDECODE / CLAUDE_PROJECT_DIR; Codex sends turn_id; Gemini CLI sets GEMINI_PROJECT_DIR;
    Cursor sends cursor_version or sets CURSOR_*; Copilot none of these."""
    if os.environ.get("CLAUDECODE") or os.environ.get("CLAUDE_PROJECT_DIR"):
        return "claude-code"
    if "turn_id" in d or any(k.startswith("CODEX_") for k in os.environ):
        return "codex"
    if os.environ.get("GEMINI_PROJECT_DIR") or os.environ.get("GEMINI_CLI"):
        return "gemini"
    if "cursor_version" in d or any(k.startswith("CURSOR_") for k in os.environ):
        return "cursor"
    if d.get("toolName") or d.get("tool_name") or d.get("hook_event_name") or d.get("hookEventName"):
        return "copilot"
    return os.environ.get("NOGAMY_AGENT", "script")


def emit(event, hook_input=None, **fields):
    try:
        root = repo_root()
        pid, mode = project_settings(root)
        if mode == "off":
            return
        user = git_user(root)
        if mode == "anonymous":
            user = hashlib.sha256(("nogamy:" + user).encode()).hexdigest()[:16]
        d = hook_input or {}
        rec = {
            "ts": datetime.now(timezone.utc).isoformat(timespec="seconds"),
            "event": event,
            "project": pid,
            "core_version": core_version(root),
            "agent": agent_name(d),
            "session": str(d.get("session_id") or d.get("sessionId") or ""),
            "user": user,
            **fields,
        }
        HOME.mkdir(parents=True, exist_ok=True)
        if LOG.exists() and LOG.stat().st_size > MAX_LOG_BYTES:
            LOG.replace(LOG.with_suffix(".old.jsonl"))
        line = json.dumps(rec, ensure_ascii=False) + "\n"
        with LOG.open("a", encoding="utf-8") as f:
            f.write(line)
        if os.environ.get("NOGAMY_TELEMETRY_URL"):
            with QUEUE.open("a", encoding="utf-8") as f:
                f.write(line)
            _spawn_flush()
    except Exception:  # telemetry must never break the agent
        pass


def _spawn_flush():
    flags = 0
    if os.name == "nt":
        flags = subprocess.DETACHED_PROCESS | subprocess.CREATE_NEW_PROCESS_GROUP
    subprocess.Popen([sys.executable, str(Path(__file__).resolve()), "--flush"],
                     stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
                     creationflags=flags, close_fds=True)


def flush():
    """Post queued events as one JSON array. Keeps the queue on failure (retried next time)."""
    url = os.environ.get("NOGAMY_TELEMETRY_URL")
    if not url or not QUEUE.exists():
        return
    try:
        fd = os.open(LOCK, os.O_CREAT | os.O_EXCL)
        os.close(fd)
    except FileExistsError:
        if time.time() - LOCK.stat().st_mtime < 60:
            return
    try:
        batch = QUEUE.with_suffix(".sending.jsonl")
        if not batch.exists():
            QUEUE.replace(batch)
        events = [json.loads(x) for x in batch.read_text(encoding="utf-8").splitlines() if x.strip()]
        req = urllib.request.Request(url, data=json.dumps(events).encode(), method="POST",
                                     headers={"Content-Type": "application/json"})
        if os.environ.get("NOGAMY_TELEMETRY_AUTH"):
            req.add_header("Authorization", os.environ["NOGAMY_TELEMETRY_AUTH"])
        urllib.request.urlopen(req, timeout=10).close()
        batch.unlink()
    except Exception:
        pass
    finally:
        LOCK.unlink(missing_ok=True)


if __name__ == "__main__" and "--flush" in sys.argv:
    flush()
