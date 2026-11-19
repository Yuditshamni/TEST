# How we work in this repo

For anyone joining: the systems analyst, the data engineer, the BI developer, and any AI tool.

## The idea in three lines

1. Everything is text in Git: specs, code, the BI model, the decisions.
2. The analyst writes the spec once. The AI builds it and checks it in DEV, or hands a person a run sheet. A person approves.
3. Nothing reaches the main branch without a review. Nothing reaches TEST or PROD without a person.

## Where things go

| You have… | Put it in |
|---|---|
| something you **received** (email, transcript, metadata, deck) | `_private/raw/`, converted to Markdown, never edited |
| a fact about a **source** table | `sources/<system>/<table>.md` |
| a spec for a **target** table | `stt/<domain>/<table>.md` |
| a term, a rule, who-sees-what | `_context/glossary.md`, `business-rules.md`, `access-rules.md` |
| a measure from the system we replace | `_context/legacy-measures.md` |
| an unanswered question | `_context/open-questions.md`, with an owner |
| a decision | `_context/architecture.md` + a line in `_context/decisions-log.md` |
| people, e-mails, who has which access | `_context/people-and-access.md` (never a phone) |
| a platform fact (technology, environment, Git, promotion) | `_context/platform.md` |
| a table, view, procedure | `db/<SCHEMA>/<Type>/<OBJECT>.sql` |
| an ingestion or orchestration item | `etl/<project>/<NN_layer>/` |
| any database change (with its object file) | `scripts/migrations/NNNN_<what>.sql` |
| grants, config rows | `scripts/grants/`, `scripts/seed/` |
| a semantic model or report | `bi/<project>/` |
| a report spec or mockup | `ui/<report>/` |
| data checks / test document of a deploy / golden questions | `qa/data/`, `qa/deploy/`, `qa/golden/` |
| something to **send to people** | `_private/docs/` |
| a **final, signed or approved** document (architecture, specs, signed STT, signed tests) | `docs/` |

## The daily loop

```
task → AI plans → you approve → AI builds in a branch → runs in DEV, or gives you a run sheet → checks
     → commit → you review → PR → merge → promotion to TEST → promotion to PROD
```

- How far the AI runs things by itself: the access level in `_context/platform.md` §7 (`AGENTS.md`, "What the AI can run here").
- How a change is promoted (by hand, a platform tool, CI/CD), and who does it: `_context/platform.md` §5, skill `nogamy-deploy`.
- Branch per topic. Commit small; the message says why. PR even for your own files; the `nogamy-review` skill runs first, then a person.

## Ownership

| Folder | Owner |
|---|---|
| `sources/`, `stt/` (business columns), `_context/glossary.md`, `business-rules.md`, `access-rules.md`, `legacy-measures.md`, `qa/golden/` | systems analyst |
| `stt/` (technical columns), `db/`, `etl/`, `scripts/`, `tools/project/`, project skills (`.claude/skills/<project-id>-*`), `PROJECT.md`, `_context/platform.md`, `architecture.md`, `open-questions.md` | data engineer |
| `bi/` (measures, security, reports), `ui/` | BI developer |
| `standards/` | Nogamy (read-only here) |

## The systems analyst, from day one

The analyst works in the repo before any code exists.

| When | Does | Skill |
|---|---|---|
| a meeting, email or document arrives | puts it in `_private/raw/`; the AI lists decisions, questions, terms and rules; the analyst approves the list | `nogamy-project-memory` |
| meeting a source system | one file per source table; the AI fills the technical part from a profile, the analyst the meaning | `nogamy-specs`, `nogamy-explore-data` |
| an existing BI or ETL system is replaced | its scripts and metadata become sources, joins, rules and measures | `nogamy-legacy-migration` |
| defining what to build | one STT per target table; `status: approved` is the green light to build | `nogamy-specs` |
| the client asks a business question | it becomes a golden question with a known answer | `nogamy-qa-checks` |
| before anything is sent | read it as the client | `nogamy-client-readout` |

## What AI may and may not do here

| May | May not |
|---|---|
| write SQL, ETL items, model files, checks, descriptions | touch TEST or PROD |
| run in DEV what its access level allows; read structure and counts | promote, delete objects or data |
| review a change and block it | change permissions |
| update `_context/` after a meeting (after you approve the list) | see real rows of people or customers |
