---
name: nogamy-project-memory
description: Read and update the project memory in PROJECT.md and _context/. Use at the start of every task, when a decision is made, when a question opens or closes, when material arrives (email, document, metadata), and after every meeting (transcript or notes → updates to PROJECT.md and _context/).
---

# Project memory

The AI does not remember between sessions. `PROJECT.md` and `_context/` do. A fact that lives only in a chat is lost.

## Read order, every session

The read order is in `AGENTS.md` (single source): `AGENTS.md`, then `PROJECT.md`, then `_context/`. Follow it before every task.

## Where a fact goes

| Fact | File | Owner |
|---|---|---|
| client, project id, packs, scope, environments by name | `PROJECT.md` → Identity, Environments | data engineer |
| people and roles (who decides what) | `PROJECT.md` → People and roles | data engineer |
| a skill or agent written for this project | `PROJECT.md` → Project skills / Project agents | data engineer |
| a command the agents may run | `PROJECT.md` → Agent tools | data engineer |
| a rule for this project (stricter than the core, never looser) | `PROJECT.md` → Project rules | data engineer |
| technology, environments, Git, promotion, AI access | `_context/platform.md` | data engineer |
| how the team works with an AI | `_context/working-agreement.md` | project lead |
| decision, current state of the design | `_context/architecture.md` | data engineer |
| a deviation from the base method | `_context/architecture.md` → Deviations from the base (`nogamy-method`) | architect |
| why / when it was decided | `_context/decisions-log.md` (append, dated) | data engineer |
| not decided yet | `_context/open-questions.md`, with owner and what it blocks | data engineer |
| business term + synonyms | `_context/glossary.md` | systems analyst |
| business rule | `_context/business-rules.md` (`BR-NNN`) | systems analyst |
| who sees which rows and columns | `_context/access-rules.md` | systems analyst |
| a measure of the legacy system + its meaning | `_context/legacy-measures.md` | systems analyst |
| a fact about a source table | `sources/<system>/<table>.md` | systems analyst |
| a verified fact about the platform | `_context/platform-facts.md` | AI (`nogamy-platform-watch`) |
| people detail (name, role, e-mail; never a phone), how access works (never secrets) | `_context/people-and-access.md` | data engineer |
| anything received as is | `_private/raw/` (never edited) | everyone |

One fact, one place. Everywhere else links to it.

**Older projects** keep the two files in `_private/context/`. Found there and missing in `_context/` → propose moving them (a PR): phone numbers, commercial terms and commentary on people are removed first, and stay in `_private/`.

**Core files are not memory.** `nogamy-*` skills, `AGENTS.md`, `standards/`, `tools/`, `nogamy/` are read-only in a project. A fact never goes into them. A wish to change one → `nogamy-feedback`.

## When material arrives

1. Convert it to Markdown: the content as received, not summarized, not corrected. The original file stays outside the repo.
2. Save it: `_private/raw/emails/`, `_private/raw/meetings/<YYYY-MM-DD> <title>/`, or `_private/raw/reference/`.
3. Sensitive rows inside it (people, customers) are removed or masked **before** it is saved.

## After a meeting, or a new document (sync)

Input: a transcript or notes in `_private/raw/meetings/<YYYY-MM-DD> <title>/`.

1. List: decisions · new questions · answered questions · new terms · new rules · facts about sources · changes to people, roles or project rules · action items with owner.
2. **Show the list to the developer before editing anything.**
3. After approval, update the files above. Action items with an owner go to `open-questions.md`.
4. Commit (when asked): `context: sync <meeting> <date>`.

## When a decision is made

Same commit:
1. update the section in `architecture.md` (or `platform.md`, or `PROJECT.md` → Project rules);
2. append a dated line to `_context/decisions-log.md`: what, who decided, why;
3. delete the item from `open-questions.md` if it was there.

An architecture decision belongs to the architect (`PROJECT.md` → People and roles). If a task needs one that is still open: stop, name the decision and its owner, do not decide.

## Never

- Write secrets, passwords or connection strings with credentials.
- Copy real rows of people or customers into any file.
- Edit `_private/raw/`.
- Leave an open question inside a spec. It goes to `open-questions.md`.
- Quote internal content from `_private/` (people commentary, commercial terms) into a committed file.
- Let anything about the client leave the project: not in feedback, not in telemetry, not in a core file.
