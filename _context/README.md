# _context/ — the project's memory

What an AI (or a new team member) reads to understand the project. Written for the machine: structured, explicit, one fact in one place. The AI does not remember between sessions; these files do.

| File | What | Owner |
|---|---|---|
| `platform.md` | The technology, environments, Git, promotion, what the AI may reach | data engineer |
| `architecture.md` | Current truth: layers, locked decisions, the model | data engineer |
| `decisions-log.md` | Why and when each decision was made, including reversed ones (append only) | data engineer |
| `open-questions.md` | What is not decided, who owns it, what it blocks | data engineer |
| `people-and-access.md` | Who is who, who approves what, how access works (e-mail yes, phone never) | data engineer |
| `working-agreement.md` | How the team works with an AI | project lead |
| `glossary.md` | Business terms, definitions, synonyms | systems analyst |
| `business-rules.md` | Rules that live in people's heads today | systems analyst |
| `access-rules.md` | Who may see which rows and columns | systems analyst |
| `legacy-measures.md` | Every measure of the system we replace, with its business meaning | systems analyst |
| `platform-facts.md` | Platform facts we depend on, verified in the official docs, re-checked | AI (`nogamy-platform-watch`) |

Rules:
- English structure, business values in the client's language.
- When a question closes, move the answer to its file and delete it from `open-questions.md`.
- Material as received is not here: `_private/raw/`.
- Nothing internal (people commentary, commercial terms) in this folder: it is committed.
