# Usage events — what is measured, and what never is

The hook `nogamy/hooks/nogamy_hook.py` writes one line per event to `~/.nogamy/usage.jsonl` on the
developer's machine. The daily core check uploads new lines to the core repo, branch `usage-data`.
The weekly curator turns them into the core report (an issue labeled `core-report` in the core repo).

## Events

| Event | When | Extra fields |
|---|---|---|
| `session_start` | an agent session starts in a Nogamy repo | — |
| `skill_used` | the agent reads a `SKILL.md` (file read, shell read, Copilot `skill` tool) | `skill`, `kind` (core / project) |
| `core_edit_blocked` | the hook blocked a write to a core file | `core_path` |
| `skill_gate_blocked` | the hook blocked a write before its skill was read | `skill` |
| `core_update_checked` / `_applied` / `_declined` | the daily core check | `latest`, `version` |
| `feedback_sent` / `feedback_blocked` | `nogamy-feedback` | `skill` / number of reasons |

Every event also has: `ts`, `project` (the project id from `PROJECT.md`), `core_version`, `agent`
(claude-code / copilot / codex), `session`, `user` (git `user.email`).

## Never collected

Prompts, answers, file contents, data, query results, file paths outside core files, repo or org names.

## Modes (`PROJECT.md` → `Telemetry:`)

- `on` — as above.
- `anonymous` — `user` is a one-way hash; usage per person cannot be seen.
- `off` — nothing is written or sent. Use when the client contract requires it.
- Per developer: environment variable `NOGAMY_TELEMETRY_MODE` overrides (e.g. `off`).

## Optional live endpoint

If `NOGAMY_TELEMETRY_URL` is set (e.g. a Fabric Eventstream custom endpoint for a live Power BI view),
events are also posted there as a JSON array, by a detached process, so the agent never waits.
Optional header: `NOGAMY_TELEMETRY_AUTH`. Unset = GitHub upload only.

## Transparency

Developers are told on onboarding that skill usage is measured, what is measured, and why:
to see which parts of the method help, which are missing, and which nobody uses.
