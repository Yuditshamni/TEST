---
name: nogamy-platform-watch
description: Verify platform facts in the official documentation before relying on them, record them in _context/platform-facts.md, and re-check once a day the ones that can expire (a missing feature we work around, a preview we rely on, a limit that shapes the design). Use before stating any platform fact, when filling a platform skill, at the first session of the day (when last_checked in _context/platform-facts.md is not today), or when asked "what's new" in the platform.
---

# Platform facts: verify, record, re-check

Our decisions rest on facts about the platform. A fact from memory may be wrong, or true last year. Cloud platforms change every month. This skill keeps the facts honest.

Needs `_context/platform-facts.md` and the official documentation named in `_context/platform.md` §2. The platform's own source and watch topics: `references/<platform>.md` in this folder (shipped: `fabric.md`, `sqlserver.md`, `adf.md`, `airflow.md`).

## 1. Verify before relying (always)

Any platform fact — a feature's status, a limit, a syntax, an API — is checked before it enters a plan, a skill or code.

| The AI has | Then |
|---|---|
| a docs connector (MCP) or web access | search the official documentation; quote the link |
| no access to the docs | say "not verified", and ask the person to check the named page; or prove it with a harmless test in DEV |

- Only the official documentation counts. No blogs, no forum answers, no guesses.
- Docs and reality disagree? What was tested in DEV wins, and both are written down.
- A verified fact others will need → a row in **Verified facts** of `_context/platform-facts.md`, with its source.
- An assumption nobody verified → **Not tested yet**. It is not a fact.

## 2. Daily re-check

**When:** the first session of the day. Read `last_checked` in `_context/platform-facts.md`; not today → run this **before** the task, then continue. It takes a few minutes and needs no access to the platform, only to its docs. Also when asked "what's new".

1. Read the platform's "what's new" or release notes, and search the docs for each item in the **watch list**.
2. For each item, compare what the docs say today with the `Known` column.
3. Changed → a dated line in the **log**: what changed, the link, which file or decision it affects.
4. A change that touches a decision (`_context/architecture.md`, `_context/platform.md`, a skill, `AGENTS.md`):
   - do **not** change the decision;
   - add or update the item in `_context/open-questions.md`, with its owner;
   - tell the developer in one line at the start of the reply.
   - A core file (a `nogamy-*` skill, `AGENTS.md`, `standards/`) is read-only here → `nogamy-feedback`, with no client detail.
5. A new feature relevant to what we build → add it to the watch list.
6. Set `last_checked` to today. Commit on the current branch (when asked): `context: platform check <date>`.

## Rules

- Every line has a source: a link, or `tested in DEV <date>`.
- Nothing changed → only `last_checked` moves. No noise in the log.
- Never act on a finding (no code change, no setting change) without the developer.
- What belongs on the watch list: something we would do differently if it changed. Not general news.
- No docs access today → say so in one line, leave `last_checked` as it is, and go on with the task.
