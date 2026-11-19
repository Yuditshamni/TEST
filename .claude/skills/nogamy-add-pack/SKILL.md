---
name: nogamy-add-pack
description: Add a platform pack (Fabric today) to this project — the framework objects, tools, MCP server and starting files that only that platform needs — as a PR the developer merges. Use when the session-start hook says a pack is missing, when a skill finds tools/fabric/ or tools/migrate/ missing, or when the work involves Microsoft Fabric, a Fabric workspace, Warehouse, Lakehouse, OneLake, Data Factory pipelines or a semantic model and PROJECT.md has no "Packs: fabric"; also on "add Fabric", "הוסף פאבריק", "חבילת Fabric".
---

# Add a platform pack

A new project starts with the core only. Platform files (framework objects, tools, MCP) come as a **pack**, added once, when the project uses that platform.
The platform's skills are always in the core. A skill that needs a pack file and does not find it sends the agent here.

## Packs

| Pack | Adds | Defined in |
|---|---|---|
| `fabric` | the framework objects in `fabric/` (`fabric/README.md`, the `MNG` / `QA` tables, `SP_DQA`, `GPL_DQA`), `tools/fabric/`, `tools/migrate/`, the `microsoft-learn` MCP server (`.mcp.json`, `.vscode/mcp.json`) | `nogamy/packs/fabric.txt` |

Installed packs are listed in `PROJECT.md` → Identity → `Packs:`. A pack's files are core files from then on: read-only, updated by `nogamy-core-update`.
A platform with no pack yet works with the generic skills and `_context/platform.md`. A new pack is a core change: `nogamy-feedback`.

## When

- The session-start hook says "pack `<name>` is missing".
- The developer starts work on the platform and the pack is not in `PROJECT.md` → `Packs:`.
- A skill's `references/fabric.md` needs a pack file (`tools/fabric/`, `tools/migrate/`, the framework objects) and it is missing.
- The developer asks for it.

Already installed → say so in one line and go on with the task.

## Steps

1. Tell the developer in at most 3 short lines: what the pack adds (table above), that it comes as a PR, and that nothing in the project is overwritten.
   Ask: "Add the `<name>` pack now?" (options: yes / not now).
2. Yes → ask for the values the pack needs, in one question each, and only those still empty in `PROJECT.md` → Environments:
   - `fabric`: the DEV, TEST and PROD workspace names; the AI identity for DEV.
   Unknown → leave the placeholder; it becomes an open question in step 3. Never guess a name.
   Do not edit `PROJECT.md` yourself: `add-pack` stops on uncommitted changes. The values go in as parameters.
3. Run, with one `--set` per known value and one `--open-question` per unknown one:
   ```
   python nogamy/ops/core_update.py add-pack --name fabric \
     --set "DEV=<name>" --set "TEST=<name>" --set "PROD=<name>" \
     --set "AI identity (DEV only)=<name>" --open-question "<what is unknown, and who owns it>"
   ```
   - `--set` replaces the value of a line that already exists in `PROJECT.md` (the label before the colon). A missing line → it stops with an error: show it to the developer, do not add the line by hand.
   - `--open-question` is written to `_context/open-questions.md` inside the same PR.
   - Uncommitted changes → it stops. Ask the developer to commit or stash; never stash for them.
   - It creates `nogamy/add-pack-<name>`, copies the pack from the project's core version, adds `<name>` to `Packs:`, pushes, opens the PR, and returns to the original branch.
4. Give the PR link. Say: "Review and merge it yourself. The pack's tools are there after the merge."
5. Not now → `python nogamy/ops/core_update.py pack-decline --name <name>`, then one line. The hook stays quiet for 7 days. Without the command it asks again tomorrow.

## Rules

- Never copy pack files by hand, never from another project. Only `add-pack`, from the core release.
- Never edit a pack file after it is added: it is core. A wish to change it → `nogamy-feedback`. Seed files (`+` in the pack list) belong to the project after they are added.
- Never write a real workspace name, tenant or identity into a core file. They go only to `PROJECT.md`.
- `gh` not logged in, or no access to the core repo → say so in one line (`gh auth login`) and go on with the task.
- The project does not use the platform, or the developer said no → do not offer it again in this session.

## Output

One of: the PR link; "pack already installed"; "not now". Plus the open questions written in step 2, if any.
