# platform-facts.md — platform facts we depend on

Maintained by the `nogamy-platform-watch` skill. Our decisions rest on facts about the platform; cloud platforms change, so a fact has a source and a date, and the ones that can expire are re-checked.
A change here never changes a decision by itself: it opens an item in `open-questions.md`.

last_checked: never
Checked once a day, at the first session of the day, when `last_checked` is not today (`AGENTS.md` → Daily). Watch list for a platform with a core reference: `.claude/skills/nogamy-platform-watch/references/<platform>.md`.

## Verified facts

What a developer new to this platform must know. One line per fact. Source = a link to the official docs, or `tested in DEV` with the date.

| # | Area | Fact | Source |
|---|---|---|---|
| F1 | | | |

Areas to cover at setup: data types and limits · constraints and indexes · transactions and concurrency · what is saved in Git and what is not · what a deployment moves and what it does not · backup and restore · permissions and roles · quirks of the connection from each source.

## Watch list

Facts that can expire: a missing feature we work around, a preview we rely on, a limit that shapes the design.

| # | Topic | Known (as of last check) | Affects |
|---|---|---|---|
| W1 | | | |

## Not tested yet

What we assume without having verified. Each line becomes a verified fact, or an open question.

## Log

| Date | Item | What changed | Link | Action |
|---|---|---|---|---|
