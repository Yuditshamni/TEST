# nogamy-platform-watch — Microsoft Fabric

Read when `_context/platform.md` §2 names Microsoft Fabric.

## Source: Microsoft Learn, through its MCP server

The only source for Fabric facts is Microsoft Learn. The Fabric pack ships its MCP server (read-only, no login):

| File | Entry |
|---|---|
| `.mcp.json` (Claude Code) | `"mcpServers": { "microsoft-learn": { "type": "http", "url": "https://learn.microsoft.com/api/mcp" } }` |
| `.vscode/mcp.json` (VS Code, GitHub Copilot) | `"servers": { "microsoft-learn": { "type": "http", "url": "https://learn.microsoft.com/api/mcp" } }` |

Tools: `microsoft_docs_search` (find the page), `microsoft_docs_fetch` (read it). No MCP in this session → the Learn pages by web access, or "not verified".

Start of each daily check: the Fabric "What's new" pages on Learn, then each watch-list item.

## Watch list topics

What the core cares about on Fabric. A project adds rows for what it relies on; each row says what we would do differently if it changed.

| Topic | Why we watch it |
|---|---|
| Fabric Warehouse: T-SQL surface (`ALTER TABLE ... ALTER COLUMN` in preview, `MERGE`, temp tables — `##global` not supported, constraints `NOT ENFORCED`) | shapes migrations and load procedures (`nogamy-db-objects`, `nogamy-bronze-load`) |
| Data Factory pipelines: activities, connections (`ServicePrincipal` / `WorkspaceIdentity` accepted by the API, `OAuth2` only in the portal), Copy data types | shapes ingestion (`nogamy-build-pipeline`) |
| Deployment pipelines | the core promotes by a CI/CD runner instead; a change may reopen that choice (`nogamy-deploy`) |
| Git integration: which items it saves, the folder format | the repo layout under `fabric/` and the drift check (`nogamy-git-workflow`, `nogamy-dev-workflow`) |
| Variable library | per-environment values in pipelines (`nogamy-deploy`) |
| Power BI: TMDL, PBIR, Direct Lake (rebinding, fallback to DirectQuery) | the semantic model's defaults (`nogamy-semantic-model`) |
| Fabric Data Agent, Copilot | how an AI assistant reads the model, and what it needs from it (`nogamy-semantic-model`) |
| Fabric REST APIs used by `tools/fabric/` | the agent's DEV loop (`nogamy-dev-workflow`) |

## Facts file

On Fabric the facts live in `_context/platform-facts.md` like on any platform. An older project may still have `_context/fabric-watch.md` (same columns: watch list, log, `last_checked`): move its rows into `platform-facts.md` in a `context:` PR, and read only the new file after that.
