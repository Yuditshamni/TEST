"""Hook tests: run nogamy_hook.main() on fake events, in core mode and in simulated project mode."""
import io
import json
import os
import sys
import tempfile
from contextlib import redirect_stdout, redirect_stderr
from pathlib import Path

ROOT = Path(sys.argv[1]).resolve() if len(sys.argv) > 1 else Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "nogamy" / "hooks"))
os.environ["NOGAMY_TELEMETRY_MODE"] = "off"
import nogamy_hook as h  # noqa: E402

tmp = Path(tempfile.mkdtemp())
no_skill = tmp / "t1.jsonl"
no_skill.write_text("", encoding="utf-8")
with_skill = tmp / "t2.jsonl"
with_skill.write_text(json.dumps({"type": "assistant", "message": {"content": [
    {"type": "tool_use", "name": "Read", "input": {"file_path": str(ROOT / ".claude/skills/nogamy-db-objects/SKILL.md")}}]}}) + "\n",
    encoding="utf-8")


def run(ev):
    sys.stdin = io.StringIO(json.dumps(ev))
    out, err = io.StringIO(), io.StringIO()
    with redirect_stdout(out), redirect_stderr(err):
        code = h.safe_main()
    return code, (err.getvalue() or out.getvalue()).strip()[:110]


def w(path, transcript=None):
    ev = {"hook_event_name": "PreToolUse", "tool_name": "Write", "tool_input": {"file_path": str(ROOT / path), "content": "x"}}
    if transcript:
        ev["transcript_path"] = str(transcript)
    return ev


cases = [
    ("core repo: edit a core skill is allowed", w(".claude/skills/nogamy-naming/SKILL.md"), 0),
    ("SQL in db/ without the skill -> blocked", w("db/SILVER/Views/V_X.sql", no_skill), 2),
    ("SQL in db/ after reading nogamy-db-objects -> allowed", w("db/SILVER/Views/V_X.sql", with_skill), 0),
    ("SQL in fabric/data/ without the skill -> blocked", w("fabric/data/WH_DWH.Warehouse/GOLD/Tables/X.sql", no_skill), 2),
    ("a README write is free", w("_context/glossary.md", no_skill), 0),
    ("read base_prompt whole -> blocked", {"hook_event_name": "PreToolUse", "tool_name": "Read",
                                           "tool_input": {"file_path": str(ROOT / "standards/base_prompt.md")}}, 2),
    ("read base_prompt by range -> allowed", {"hook_event_name": "PreToolUse", "tool_name": "Read",
                                              "tool_input": {"file_path": str(ROOT / "standards/base_prompt.md"), "limit": 40}}, 0),
]
fails = 0
for name, ev, want in cases:
    code, msg = run(ev)
    ok = code == want
    fails += not ok
    print(f"{'PASS' if ok else 'FAIL'}  {name}  (exit {code}) {msg if code else ''}")

# Simulated project: lock on
h.in_core_repo = lambda: False
for name, ev, want in [
    ("project: edit a core skill -> blocked", w(".claude/skills/nogamy-naming/SKILL.md"), 2),
    ("project: edit AGENTS.md -> blocked", w("AGENTS.md"), 2),
    ("project: shell write into tools/ -> blocked", {"hook_event_name": "PreToolUse", "tool_name": "Bash",
                                                     "tool_input": {"command": "echo x > tools/dev_map.py"}}, 2),
    ("project: edit PROJECT.md -> allowed", w("PROJECT.md"), 0),
    ("project: a project skill -> allowed", w(".claude/skills/acme-hr-payroll/SKILL.md"), 0),
    ("project: _context/platform.md -> allowed", w("_context/platform.md"), 0),
    ("project, Gemini: write_file to a core skill -> blocked", {"hook_event_name": "BeforeTool", "tool_name": "write_file",
        "tool_input": {"file_path": str(ROOT / ".claude/skills/nogamy-naming/SKILL.md"), "content": "x"}}, 2),
    ("project, Gemini: run_shell_command into tools/ -> blocked", {"hook_event_name": "BeforeTool",
        "tool_name": "run_shell_command", "tool_input": {"command": "echo x > tools/dev_map.py"}}, 2),
    ("project, Cursor: shell write into AGENTS.md -> blocked", {"hook_event_name": "beforeShellExecution",
        "command": "echo x >> AGENTS.md"}, 2),
    ("project, Copilot CLI: toolArgs as JSON text -> blocked", {"hookEventName": "preToolUse", "toolName": "edit",
        "toolArgs": json.dumps({"path": str(ROOT / "AGENTS.md")})}, 2),
    ("project, Gemini: write_file to PROJECT.md -> allowed", {"hook_event_name": "BeforeTool", "tool_name": "write_file",
        "tool_input": {"file_path": str(ROOT / "PROJECT.md"), "content": "x"}}, 0),
]:
    code, msg = run(ev)
    ok = code == want
    fails += not ok
    print(f"{'PASS' if ok else 'FAIL'}  {name}  (exit {code}) {msg if code else ''}")
# a bug inside the hook never blocks the work
real = h.core_lock
h.core_lock = lambda d, m: 1 / 0
code, msg = run(w(".claude/skills/nogamy-naming/SKILL.md"))
h.core_lock = real
ok = code == 0 and "Nogamy hook error" in msg
fails += not ok
print(f"{'PASS' if ok else 'FAIL'}  a crash inside the hook -> the call goes on, the error is reported  (exit {code})")
print("FAILS:", fails)
sys.exit(1 if fails else 0)
