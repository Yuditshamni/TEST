# nogamy/upgrades/ — changes to a project's own files when the core changes their shape

Core files are replaced by a core update. Project files (`PROJECT.md`, `_context/`) are never replaced:
when a core version changes their expected shape (a new section, a renamed row), an upgrade here adapts
each project's copy, and the core-update PR shows what it changed for a person to review.

| Rule | |
|---|---|
| Name | `NNNN_<what>.py`; runs in number order, on every core update |
| Function | `upgrade(project: pathlib.Path) -> list[str]`: one line per change made; empty = nothing to do |
| Safe twice | checks the old shape before changing; a second run returns `[]` |
| Touches | project files only, never a core file (they are replaced anyway) and never data or secrets |
| Adds, never removes | project content is kept; a section is added or a row renamed, never deleted |
| Docstring | first line = what it does, shown in the PR summary |
| Test | a case in `nogamy/tests/test_upgrades.py` |

Run by `nogamy/ops/core_sync.py` after the core files are copied. A failing upgrade stops the core update
(no PR), with its error.
