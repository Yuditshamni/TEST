# _private/ — local only, never committed

Everything in this folder except this file is ignored by Git (`.gitignore`). It exists on the machines of the people who work on the project, and wherever the team backs it up.

The `nogamy-project-setup` skill creates the folders below. Decisions and people are not here: they are committed, in `_context/`.

| Folder / file | What |
|---|---|
| `raw/` | material **as received**, converted to Markdown on arrival, never edited: `emails/`, `meetings/<YYYY-MM-DD> <title>/`, `reference/` (client documents, metadata exports, legacy scripts). The original file stays outside the repo |
| `docs/` | outputs **for people**: architecture document, presentations, STT exported for sign-off (`docs/specs/`). Not a source of truth for anything the AI builds from. The final signed or approved version is copied to the committed `docs/` at the repo root |
| `sandbox/` | scratch work |
| `<tool>_identity.json` | the AI's identity config for tools that connect (server names, allow list). The secret itself is in the operating system's credential store |

Rules:
- When something in `raw/` changes what we know, the change is written into the structured files in `_context/` (`project-memory` skill), not here.
- An AI tool may read this folder for context. It never quotes internal content (people commentary, commercial terms) into a committed file without an explicit OK.
- Project facts the whole team needs do not belong here: they go to `_context/`.
