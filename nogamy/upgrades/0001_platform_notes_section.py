"""Adds `## 10. Platform notes per skill` to _context/platform.md (projects set up before core v0.1.0)."""
from pathlib import Path

SECTION = """
## 10. Platform notes per skill

What this project adds to, or overrides in, a skill's platform facts. Same topics as the skill's `Platform specifics` table.
Only what differs from the core reference. A fact every project on this platform needs → `nogamy-feedback`, so it enters the core reference.

<Add a heading per skill (### nogamy-<skill>) with a two-column table, only when there is something to say.>
"""


def upgrade(project: Path) -> list:
    f = Path(project, "_context/platform.md")
    if not f.exists():
        return []
    text = f.read_text(encoding="utf-8")
    if "## 10." in text or "Platform notes per skill" in text:
        return []
    f.write_text(text.rstrip("\n") + "\n" + SECTION, encoding="utf-8")
    return ["_context/platform.md: added section 10, Platform notes per skill"]
