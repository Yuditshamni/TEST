# working-agreement.md — how the team works with an AI

Binding for every AI tool in the repo. The defaults are Nogamy's; the project lead changes them at setup (`nogamy-project-setup`), in this file.

## Communication

**What works**
- Direct and to the point. No flattery, no opening pleasantries.
- Answer the question before anything else.
- Call things by their name. If the developer is wrong, say so directly and immediately.
- When you are wrong: admit it, correct it, move on. No long apologies.
- Verify before agreeing: repeat the example and confirm you understood.
- One question at a time, with multiple-choice options at decision points.
- Do not invent requirements. Do not invent problems to look thorough.

**What does not work**
- Ground-up explanations of BI, ETL or modelling to people who do this for a living.
- Flooding a simple answer with bullets and headers.
- Building everything in a final version and then asking for approval. Propose, get approval, implement.
- Repeating what was said before answering.

## Interpreting requests

| When the developer says | It means |
|---|---|
| "Update" | edit the existing file. Never create a parallel one |
| "Bring me everything" | all the relevant files, not one |
| "Last word" / "final" | a locked baseline. Do not touch without an explicit request |
| "Like" / "as if" | an unripe idea: discuss before implementing |

## Work patterns

- **Iterative:** propose → approve or correct → implement → next. No leaps.
- **Proof of concept before code:** prove a connection or an API call by hand first, then build on it.
- Open questions are written in `open-questions.md` with an owner. They do not stay inside a spec.
- Consolidated updates (diagrams, summaries) at the end of a session, not in the middle.

## Deliverables for people

- Project default: <Excel for specs and mappings; the client's language, right to left where it applies; minimal design>.
- CSV: UTF-8 with BOM, `snake_case` headers, ISO 8601 dates, `TRUE` / `FALSE`.
- Outputs for people live in `_private/docs/` and are edited only on an explicit request.

## Repo rules for any AI tool

1. **Read first:** the read order in `AGENTS.md`.
2. **Small, focused commits**, in English: `<scope>: <what> — <why>`. Never commit a file unrelated to the task.
3. **No secrets**: no passwords, keys or connection strings with credentials. Templates with placeholders only.
4. **An architecture change = stop.** A task that needs a deviation from `architecture.md`: do not do it, ask. A decision that closed: update `architecture.md` and the decisions log in the same commit.
5. **A check that compares definitions does not prove it works.** After a change is in DEV, run it.
6. **Check prerequisites before a change others depend on.** Change one, run it, then the rest.
7. **Try before asking.** Use the access you were given, and ask a person only for what is really blocked, with the exact error. Running SQL that writes needs the permission level in `platform.md` §7.
