#!/bin/sh
# Core file (Nogamy). Starts nogamy_hook.py for every AI tool (Claude Code, Copilot in VS Code, Codex, Cursor,
# Gemini CLI), on macOS, Linux and Windows (Git Bash). Finds Python 3.8+ and the repo root by itself, so the
# hook config needs no interpreter name and works from any working folder.
# No Python 3: a tool call is blocked with what to install (exit 2), never silently unprotected.

root="${CLAUDE_PROJECT_DIR:-${GEMINI_PROJECT_DIR:-${CURSOR_PROJECT_DIR:-}}}"
[ -n "$root" ] && [ -f "$root/nogamy/hooks/nogamy_hook.py" ] || root="$(git rev-parse --show-toplevel 2>/dev/null)"
[ -n "$root" ] && [ -f "$root/nogamy/hooks/nogamy_hook.py" ] || root="$(cd "$(dirname "$0")/../.." && pwd)"

for py in python3 python py; do
    # The version check also skips the Windows Store "python3" stub, which exists but does not run.
    if command -v "$py" >/dev/null 2>&1 && "$py" -c "import sys; sys.exit(sys.version_info < (3, 8))" 2>/dev/null; then
        exec "$py" "$root/nogamy/hooks/nogamy_hook.py"
    fi
done

input="$(cat)"
case "$input" in
    *'"PreToolUse"'*|*'"preToolUse"'*|*'"BeforeTool"'*|*'"toolName"'*|*'"tool_name"'*)
        echo "Nogamy hook: Python 3.8 or newer was not found, so the project's protections cannot run." >&2
        echo "Install Python 3 (python.org, or the OS package manager), open a new session, and try again (START-HERE.md)." >&2
        exit 2 ;;
esac
exit 0
